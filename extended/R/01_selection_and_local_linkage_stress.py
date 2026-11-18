"""Reproducible sensitivity analysis from supplied HMDA and SDAT CSVs. No identity claims."""
import pandas as pd, numpy as np, statsmodels.formula.api as smf
from pathlib import Path
from scipy.stats import spearmanr
P=Path(__import__('os').environ.get('HMDA_SDAT_DATA_DIR', '.')).resolve(); OUT=P/'HMDA_SDAT_Sensitivity_New';OUT.mkdir(exist_ok=True)
h=pd.read_csv(P/'loan_purposes_1_state_MD(3).csv',low_memory=False,dtype={'census_tract':'string','county_code':'string','debt_to_income_ratio':'string'})
s=pd.read_csv(P/'SDAT_2025_Market_Sales_With_Census_Tracts.csv',low_memory=False,dtype={'GEOID':'string','account_id_mdp_field_acctid':'string'})
h['property_value_num']=pd.to_numeric(h.property_value,errors='coerce'); h=h.loc[(h.action_taken==1)&h.property_value_num.notna()].copy().reset_index(drop=True);h['hmda_id']=np.arange(1,len(h)+1)
s['sdat_id']=s['account_id_mdp_field_acctid'].astype('string');s['sale_price_num']=pd.to_numeric(s.sale_price_clean,errors='coerce')
links=pd.read_csv(P/'HMDA_SDAT_final_analysis_ids.csv',dtype={'sdat_id':'string'});links['hmda_id']=pd.to_numeric(links.hmda_id)
assert len(h)==62305 and len(links)==4167, (len(h),len(links))
# Verify all 4167 given IDs appear in exact tract/value matching as constructed from original data.
sel=h.merge(links,on='hmda_id',validate='one_to_one').merge(s,on='sdat_id',validate='one_to_one',suffixes=('','_sdat'))
assert (sel.census_tract.astype(str)==sel.GEOID.astype(str)).all()
assert np.allclose(sel.property_value_num,sel.sale_price_num)
for c in ('interest_rate','income','loan_term','sqft_clean','year_built_clean'):
 sel[c+'_num']=pd.to_numeric(sel[c],errors='coerce')
sel['interest_rate_num']=sel['interest_rate_num']
sel['log_property_value']=np.log(sel.property_value_num)
sel['log_income']=np.log(sel.income_num.where(sel.income_num>0))
sel['log_sqft']=np.log(sel.sqft_clean_num.where(sel.sqft_clean_num>0))
sel['property_age']=2025-sel.year_built_clean_num
sel['loan_term_num']=sel.loan_term_num
cat=['debt_to_income_ratio','occupancy_type','construction_method','total_units','county_code','grade_clean','dwelling_type']
for c in cat: sel[c]=sel[c].astype(str)
base=('log_property_value ~ interest_rate_num + log_income + C(debt_to_income_ratio) + loan_term_num + '
      'C(occupancy_type) + C(construction_method) + C(total_units) + C(county_code)')
aug=base+' + log_sqft + property_age + C(grade_clean) + C(dwelling_type)'
a=smf.ols(base,data=sel).fit();b=smf.ols(aug,data=sel).fit()
print('baseline',len(sel),a.params['interest_rate_num'],b.params['interest_rate_num'],'R2',a.rsquared_adj,b.rsquared_adj,flush=True)
assert len(b.model.endog)==4167
if abs(b.params['interest_rate_num']-(-0.04053629))>1e-5: raise ValueError('Original coefficient not reproduced')
# Diagnostics selection for exact links, final analysis complete cases.
h['in_final']=h.hmda_id.isin(links.hmda_id)
# Exact links derive from tract plus reported value with reciprocal one-to-one criterion.
keep=h[h.census_tract.notna()][['hmda_id','census_tract','property_value_num']].merge(s[['sdat_id','GEOID','sale_price_num']],left_on='census_tract',right_on='GEOID',how='inner')
exact=keep.loc[keep.property_value_num==keep.sale_price_num,['hmda_id','sdat_id']]
hc=exact.groupby('hmda_id').size();sc=exact.groupby('sdat_id').size()
ex=exact[(exact.hmda_id.map(hc)==1)&(exact.sdat_id.map(sc)==1)]
assert len(ex)==4789
h['in_exact']=h.hmda_id.isin(ex.hmda_id)
h['value_band']=pd.cut(h.property_value_num,[-np.inf,200000,350000,500000,750000,1000000,np.inf],labels=['<200k','200-350k','350-500k','500-750k','750k-1m','1m+'],right=False)
report=[]
for name,g in h.groupby('value_band',observed=True):
 report.append(dict(value_band=str(name),n=len(g),exact_links=int(g.in_exact.sum()),exact_pct=100*g.in_exact.mean(),final_n=int(g.in_final.sum()),final_pct=100*g.in_final.mean(),median_value=float(g.property_value_num.median())))
rep=pd.DataFrame(report); rep.to_csv(OUT/'selection_by_value.csv',index=False)
# Broad population vs linked, finite comparable covariates.
for c in ['interest_rate','income','loan_term']:
 h[c+'_num']=pd.to_numeric(h[c],errors='coerce')
h['log_income']=np.log(h.income_num.where(h.income_num>0))
comp=[]
for c in ['property_value_num','interest_rate_num','income_num','loan_term_num','log_income']:
 for state in [False,True]:
  x=h.loc[h.in_final==state,c].dropna(); comp.append(dict(variable=c,final_sample=state,n=len(x),mean=x.mean(),median=x.median(),sd=x.std()))
pd.DataFrame(comp).to_csv(OUT/'selection_covariate_balance.csv',index=False)
# Evaluate whether selection on observed covariates changes the A coefficient by comparing unweighted vs value-band poststratified linked OLS.
# This is explicitly NOT a causal or linkage-bias correction. Target: broader eligible HMDA sample with nonmissing model-A regressors.
h['log_property_value']=np.log(h.property_value_num)
for c in ['debt_to_income_ratio','occupancy_type','construction_method','total_units','county_code']:
 h[c]=h[c].astype(str).replace({'<NA>':np.nan,'nan':np.nan})
valid=h[['log_property_value','interest_rate_num','log_income','loan_term_num','debt_to_income_ratio','occupancy_type','construction_method','total_units','county_code']].notna().all(axis=1)
valid &= np.isfinite(h[['log_property_value','interest_rate_num','log_income','loan_term_num']]).all(axis=1)
# same R sample eligibility avoids missing categorical values converted to 'nan'.
reference=h.loc[valid].copy(); reference['value_band']=pd.cut(reference.property_value_num,[-np.inf,200000,350000,500000,750000,1000000,np.inf],right=False)
selected=reference.loc[reference.in_final].copy()
# inverse sample fraction by value bands, re-normalize to mean 1; if all cells represented, positive.
prop_ref=reference.value_band.value_counts(normalize=True);prop_sel=selected.value_band.value_counts(normalize=True)
weights={band:prop_ref.get(band,0)/prop_sel.get(band,1e-12) for band in prop_ref.index}
selected['w']=selected.value_band.map(weights).astype(float);selected['w']=selected.w/selected.w.mean()
weighted=smf.wls(base,data=selected,weights=selected.w).fit()
control=smf.ols(base,data=selected).fit()
assert len(selected)==4167
pd.DataFrame([{'analysis':'linked_A','n':len(selected),'beta_rate':control.params['interest_rate_num'],'adj_r2':control.rsquared_adj},{'analysis':'linked_A_poststratified_by_property_value','n':len(selected),'beta_rate':weighted.params['interest_rate_num'],'adj_r2':weighted.rsquared_adj},{'analysis':'full_HMDA_complete_case_A','n':len(reference),'beta_rate':smf.ols(base,data=reference).fit().params['interest_rate_num'],'adj_r2':np.nan}]).to_csv(OUT/'selection_model_comparison.csv',index=False)
# Linkage error scenarios: reassign structural covariates using actual alternative 2025 SDAT sales in same tract and +/- 5000 value.
# Preserve zero duplicates globally by sampling alternative IDs without replacement.
original_sdat=set(ex.sdat_id.astype(str)); chosen=sel[['hmda_id','census_tract','property_value_num','sdat_id']].copy()
alt=s.loc[s.GEOID.notna() & s.sale_price_num.notna(),['sdat_id','GEOID','sale_price_num','sqft_clean','year_built_clean','grade_clean','dwelling_type']].copy()
alt=alt[~alt.sdat_id.isin(original_sdat)]
alt['sqft']=pd.to_numeric(alt.sqft_clean,errors='coerce');alt['year']=pd.to_numeric(alt.year_built_clean,errors='coerce')
alt=alt.loc[(alt.sqft>0)&alt.year.notna()&alt.grade_clean.notna()&alt.dwelling_type.notna()]
# Preserve levels from original selected sample so model design dimensions do not change.
alt=alt.loc[alt.grade_clean.astype(str).isin(set(sel.grade_clean))&alt.dwelling_type.astype(str).isin(set(sel.dwelling_type))]
can=chosen.merge(alt,left_on='census_tract',right_on='GEOID',how='inner',suffixes=('','_alt'))
can=can.loc[(can.sale_price_num>=can.property_value_num-5000)&(can.sale_price_num<can.property_value_num+5000)]
can=can[can.sdat_id!=can.sdat_id_alt].drop_duplicates(['hmda_id','sdat_id_alt']).copy()
print('eligible alternatives',len(can),'ids',can.hmda_id.nunique(),flush=True)
pd.DataFrame([{'analysis_n':len(sel),'candidate_pairs':len(can),'eligible_hmda':can.hmda_id.nunique(),'pct_full_eligible':100*can.hmda_id.nunique()/len(sel),'interpretation':'Hypothetical alternatives; not observed match errors'}]).to_csv(OUT/'alternative_link_eligibility.csv',index=False)
# Efficient design: reuse original baseline and categorical feature levels; replace property-feature columns in fixed full design matrix.
import patsy
Y,X=patsy.dmatrices(aug,data=sel,return_type='dataframe'); cols=X.columns
# Keep fixed design matrix, replace specific SDAT columns for each swapped row according to original patsy design_info
info=X.design_info
positions={int(v):i for i,v in enumerate(sel.hmda_id)}
groups={int(k):v.reset_index(drop=True) for k,v in can.groupby('hmda_id')};eligible=np.array(list(groups.keys()))
# no recalculation of original regression via huge repeated statsmodels: use QR factorized? full lstsq 100 times 4167x~70 costly.
# Instead apply normal-equation updates from original X'X and X'y for only altered rows.
XtX=np.asarray(X.T@X); Xty=np.asarray(X.T@Y).reshape(-1);original_beta=float(b.params['interest_rate_num']); interest_col=list(cols).index('interest_rate_num')
original_X=X.to_numpy(); y=Y.to_numpy().reshape(-1)
struct_cols=[i for i,c in enumerate(cols) if c=='log_sqft' or c=='property_age' or c.startswith('C(grade_clean)') or c.startswith('C(dwelling_type)')]
cat_grade={name:idx for idx,name in enumerate(cols) if name.startswith('C(grade_clean)')}
cat_dw={name:idx for idx,name in enumerate(cols) if name.startswith('C(dwelling_type)')}
# use category-level mapping via patsy column syntax C(field)[T.category]
colmap={c:i for i,c in enumerate(cols)}
reps=[]; rng=np.random.default_rng(20261118)
for frac in [0.05,0.10,0.20,0.30]:
 for iteration in range(50):
  target=int(round(frac*len(eligible)))
  picked=rng.choice(eligible,size=target,replace=False)
  used=set(); rows=[]; replacements=[]
  for hid in picked:
   choices=groups[int(hid)]
   available=choices.loc[~choices.sdat_id_alt.isin(used)]
   if available.empty:continue
   c=available.iloc[int(rng.integers(len(available)))];used.add(c.sdat_id_alt)
   i=positions[int(hid)];new=original_X[i].copy()
   new[struct_cols]=0.
   new[colmap['log_sqft']]=np.log(float(c.sqft));new[colmap['property_age']]=2025-float(c.year)
   gn=f'C(grade_clean)[T.{c.grade_clean}]';dn=f'C(dwelling_type)[T.{c.dwelling_type}]'
   if gn in colmap:new[colmap[gn]]=1.
   if dn in colmap:new[colmap[dn]]=1.
   rows.append(i);replacements.append(new)
  rows=np.array(rows,dtype=int)
  if len(rows):
   old=original_X[rows];new=np.stack(replacements)
   XtX_new=XtX-old.T@old+new.T@new
   Xty_new=Xty-old.T@y[rows]+new.T@y[rows]
  else: XtX_new=XtX; Xty_new=Xty
  # rank deficiency possible; lstsq yields stable coefficient for identified interest term
  coefs=np.linalg.lstsq(XtX_new,Xty_new,rcond=1e-10)[0]
  beta=float(coefs[interest_col]);reps.append({'fraction_of_eligible':frac,'replicate':iteration+1,'target_swaps':target,'actual_swaps':len(rows),'pct_full_sample_swapped':100*len(rows)/len(sel),'beta':beta,'beta_change':beta-original_beta})
res=pd.DataFrame(reps);res.to_csv(OUT/'linkage_error_scenarios_replicates.csv',index=False)
res.groupby('fraction_of_eligible').agg(n_repetitions=('beta','size'),median_swaps=('actual_swaps','median'),median_pct_full_swapped=('pct_full_sample_swapped','median'),median_beta=('beta','median'),beta_p05=('beta',lambda x:x.quantile(.05)),beta_p95=('beta',lambda x:x.quantile(.95)),median_abs_beta_change=('beta_change',lambda x:np.median(np.abs(x)))).reset_index().to_csv(OUT/'linkage_error_scenarios_summary.csv',index=False)
print('FINISHED',OUT,flush=True)
