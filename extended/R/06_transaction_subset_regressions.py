import pandas as pd, numpy as np, statsmodels.formula.api as smf
from pathlib import Path
P=Path(__import__('os').environ.get('HMDA_SDAT_DATA_DIR', '.')).resolve(); O=P/'MD_Property_Sales_Linkage_Audit'/'subset_robustness';O.mkdir(parents=True,exist_ok=True)
h=pd.read_csv(P/'loan_purposes_1_state_MD(3).csv',low_memory=False,dtype={'census_tract':'string','county_code':'string','debt_to_income_ratio':'string'})
s=pd.read_csv(P/'SDAT_2025_Market_Sales_With_Census_Tracts.csv',low_memory=False,dtype={'GEOID':'string','account_id_mdp_field_acctid':'string'})
t=pd.read_csv(P/'Maryland_Property_Sales_2025.csv',dtype=str)
ids=pd.read_csv(P/'HMDA_SDAT_final_analysis_ids.csv',dtype={'sdat_id':'string'});ids['hmda_id']=pd.to_numeric(ids.hmda_id)
h['property_value_num']=pd.to_numeric(h.property_value,errors='coerce');h=h.loc[(h.action_taken==1)&h.property_value_num.notna()].copy().reset_index(drop=True);h['hmda_id']=np.arange(1,len(h)+1)
s['sdat_id']=s['account_id_mdp_field_acctid'].astype('string');s['sale_price_num']=pd.to_numeric(s.sale_price_clean,errors='coerce')
sel=h.merge(ids,on='hmda_id',validate='one_to_one').merge(s,on='sdat_id',validate='one_to_one',suffixes=('','_sdat'))
assert len(sel)==4167
assert (sel.census_tract.astype(str)==sel.GEOID.astype(str)).all()
assert np.allclose(sel.property_value_num,sel.sale_price_num)
datecol='sales_segment_1_transfer_date_yyyy_mm_dd_mdp_field_tradate_sdat_field_89'
sel['sdat_transfer']=sel[datecol].astype(str).str.replace(r'\D','',regex=True).str[:8]
sel['late_2025']=sel.sdat_transfer.between('20250801','20251231')
assert sel.late_2025.sum()==1909
sel['sdat_price']=pd.to_numeric(sel.sale_price_clean,errors='coerce')
t['price']=pd.to_numeric(t.CONSIDR1,errors='coerce')
t['bin']=(np.floor((t.price+2500)/5000)*5000).astype('Int64')
t['tract']=t.CT2020
# sale file corroboration at property-account + recorded transfer date + sale consideration, not HMDA validity
acct_date=set(zip(t.ACCTID,t.TRADATE))
acct_date_price=set(zip(t.ACCTID,t.TRADATE,t.price.fillna(-1)))
sel['corroborated']=[(a,d,p if pd.notna(p) else -1) in acct_date_price for a,d,p in zip(sel.sdat_id,sel.sdat_transfer,sel.sdat_price)]
assert int(sel.corroborated.sum())==1773
# All distinct accounts in same census tract and HMDA value rounded to $5k
alts=t.dropna(subset=['tract','bin','ACCTID']).groupby(['tract','bin']).ACCTID.unique().to_dict()
sel['original_bin']=sel.property_value_num.astype('Int64')
sel['candidate_accounts']=[alts.get((tract,v),[]) for tract,v in zip(sel.census_tract,sel.original_bin)]
sel['competing']=[any(z!=orig for z in a) for a,orig in zip(sel.candidate_accounts,sel.sdat_id)]
assert int(sel.loc[sel.late_2025,'competing'].sum())==185
assert int(sel.loc[sel.corroborated,'competing'].sum())==50
sel['n_candidate_accounts']=[len(v) for v in sel.candidate_accounts]
for c in ('interest_rate','income','loan_term','sqft_clean','year_built_clean'):sel[c+'_num']=pd.to_numeric(sel[c],errors='coerce')
sel['log_property_value']=np.log(sel.property_value_num);sel['log_income']=np.log(sel.income_num.where(sel.income_num>0));sel['log_sqft']=np.log(sel.sqft_clean_num.where(sel.sqft_clean_num>0));sel['property_age']=2025-sel.year_built_clean_num
cat=['debt_to_income_ratio','occupancy_type','construction_method','total_units','county_code','grade_clean','dwelling_type']
for c in cat:sel[c]=sel[c].astype(str)
base=('log_property_value ~ interest_rate_num + log_income + C(debt_to_income_ratio) + loan_term_num + C(occupancy_type) + C(construction_method) + C(total_units) + C(county_code)')
aug=base+' + log_sqft + property_age + C(grade_clean) + C(dwelling_type)'
# explicit nested groups including common period, avoiding naïve comparison of distinct-time populations
masks={
 'All original linked':pd.Series(True,index=sel.index),
 'All except late-period competing':~(sel.late_2025 & sel.competing),
 'Aug-Dec only':sel.late_2025,
 'Aug-Dec no competing':sel.late_2025 & ~sel.competing,
 'Aug-Dec corroborated':sel.late_2025 & sel.corroborated,
 'Aug-Dec corroborated & no competing':sel.late_2025 & sel.corroborated & ~sel.competing,
 'Aug-Dec competing':sel.late_2025 & sel.competing,
 'Aug-Dec not corroborated':sel.late_2025 & ~sel.corroborated,
 'Jan-Jul only (outside sales file)':~sel.late_2025,
}
rows=[]
for name,mask in masks.items():
 d=sel.loc[mask].copy()
 try:
  a=smf.ols(base,data=d).fit(); b=smf.ols(aug,data=d).fit()
  assert len(a.model.endog)==len(d)==len(b.model.endog)
  rows.append(dict(subset=name,n=len(d),beta_A=a.params['interest_rate_num'],beta_B=b.params['interest_rate_num'],attenuation_pct=100*(1-abs(b.params['interest_rate_num'])/abs(a.params['interest_rate_num'])),adj_r2_A=a.rsquared_adj,adj_r2_B=b.rsquared_adj,rank_A=np.linalg.matrix_rank(a.model.exog),cols_A=a.model.exog.shape[1],rank_B=np.linalg.matrix_rank(b.model.exog),cols_B=b.model.exog.shape[1],HC3_se_B=b.get_robustcov_results(cov_type='HC3').bse[list(b.params.index).index('interest_rate_num')]))
  print(name,len(d),rows[-1]['beta_A'],rows[-1]['beta_B'],flush=True)
 except Exception as e:print('FAILED',name,repr(e),flush=True);rows.append(dict(subset=name,n=len(d),error=str(e)))
res=pd.DataFrame(rows);res.to_csv(O/'transaction_subset_regression_results.csv',index=False)
# safe diagnostic only; do not output any private property ID
pd.DataFrame([
 dict(metric='analysis_link_pairs',value=len(sel)),
 dict(metric='late_period_pairs',value=int(sel.late_2025.sum())),
 dict(metric='late_period_competing',value=int((sel.late_2025 & sel.competing).sum())),
 dict(metric='late_period_corrob',value=int((sel.late_2025 & sel.corroborated).sum())),
 dict(metric='late_period_corrob_and_competing',value=int((sel.late_2025 & sel.corroborated & sel.competing).sum())),
 dict(metric='late_period_no_competing',value=int((sel.late_2025 & ~sel.competing).sum())),
 dict(metric='late_period_corrob_no_competing',value=int((sel.late_2025 & sel.corroborated & ~sel.competing).sum())),
]).to_csv(O/'subset_counts.csv',index=False)
print('saved',O)
