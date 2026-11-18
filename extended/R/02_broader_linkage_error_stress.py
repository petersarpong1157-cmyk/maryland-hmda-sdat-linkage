import os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1';os.environ['MKL_NUM_THREADS']='1'
import pandas as pd,numpy as np,patsy,scipy.linalg as la
from pathlib import Path
P=Path(__import__('os').environ.get('HMDA_SDAT_DATA_DIR', '.')).resolve();O=P/'HMDA_SDAT_Broader_Linkage_Stress';O.mkdir(exist_ok=True)
h=pd.read_csv(P/'loan_purposes_1_state_MD(3).csv',low_memory=False,dtype={'census_tract':'string','county_code':'string','debt_to_income_ratio':'string'})
s=pd.read_csv(P/'SDAT_2025_Market_Sales_With_Census_Tracts.csv',low_memory=False,dtype={'GEOID':'string','account_id_mdp_field_acctid':'string'})
h['property_value_num']=pd.to_numeric(h.property_value,errors='coerce');h=h.loc[(h.action_taken==1)&h.property_value_num.notna()].copy().reset_index(drop=True);h['hmda_id']=np.arange(1,len(h)+1)
s['sdat_id']=s['account_id_mdp_field_acctid'].astype('string');s['sale_price_num']=pd.to_numeric(s.sale_price_clean,errors='coerce')
links=pd.read_csv(P/'HMDA_SDAT_final_analysis_ids.csv',dtype={'sdat_id':'string'});links['hmda_id']=pd.to_numeric(links.hmda_id)
sel=h.merge(links,on='hmda_id',validate='one_to_one').merge(s,on='sdat_id',validate='one_to_one',suffixes=('','_sdat'))
assert len(sel)==4167
for c in ('interest_rate','income','loan_term','sqft_clean','year_built_clean'): sel[c+'_num']=pd.to_numeric(sel[c],errors='coerce')
sel['log_property_value']=np.log(sel.property_value_num);sel['log_income']=np.log(sel.income_num.where(sel.income_num>0));sel['log_sqft']=np.log(sel.sqft_clean_num.where(sel.sqft_clean_num>0));sel['property_age']=2025-sel.year_built_clean_num
for c in ['debt_to_income_ratio','occupancy_type','construction_method','total_units','county_code','grade_clean','dwelling_type']:sel[c]=sel[c].astype(str)
base=('log_property_value ~ interest_rate_num + log_income + C(debt_to_income_ratio) + loan_term_num + C(occupancy_type) + C(construction_method) + C(total_units) + C(county_code)')
aug=base+' + log_sqft + property_age + C(grade_clean) + C(dwelling_type)'
y,X=patsy.dmatrices(aug,data=sel,return_type='dataframe');_,A=patsy.dmatrices(base,data=sel,return_type='dataframe');Y=y.to_numpy().ravel();M=X.to_numpy();A=A.to_numpy();col=list(X.columns);ic=col.index('interest_rate_num')
coefA=la.lstsq(A,Y,lapack_driver='gelsy')[0][list(patsy.dmatrices(base,data=sel,return_type='dataframe')[1].columns).index('interest_rate_num')]
basebeta=la.lstsq(M,Y,lapack_driver='gelsy')[0][ic]
assert abs(basebeta+0.04053629)<1e-6
print('Baseline',coefA,basebeta,'matrix',M.shape,flush=True)
# Structural contribution is a bundled set; donor exchanges full feature vector including categorical indicators
struct=[i for i,c in enumerate(col) if c in ('log_sqft','property_age') or c.startswith('C(grade_clean)') or c.startswith('C(dwelling_type)')]
S=M[:,struct]; n=len(sel); counties=sel.county_code.astype(str).to_numpy();v=np.log(sel.property_value_num.to_numpy());rng=np.random.default_rng(20261118+123)
groups={k:np.flatnonzero(counties==k) for k in set(counties)}
print('min county group',min(map(len,groups.values())),'counties',len(groups),flush=True)
# Valid donor candidates for each observation that stay in same county, preferably nearest 20% by property value.
# Use all donors, regardless of whether they qualify under the original linkage rule: hypothetical unobserved false matches.
nearest=[];nearby_counts=[]
for i in range(n):
 ids=groups[counties[i]];ids=ids[ids!=i]; ds=np.abs(v[ids]-v[i]); near=ids[ds<=np.log(1.2)];
 if len(near)==0:near=ids[np.argsort(ds)[:min(20,len(ids))]]
 nearest.append(near);nearby_counts.append(len(near))
assert min(nearby_counts)>=1
# Modes: constrained to same county & within ~20% price or nearest fallback; same county unrestricted; all Maryland.
records=[]
for mode in ['county_value_near','county_any','statewide_any']:
 for frac in [0.05,0.10,0.20,0.30,0.50,1.00]:
  for rep in range(50):
   picked=rng.choice(n,size=int(round(n*frac)),replace=False)
   if mode=='county_value_near':donors=np.array([rng.choice(nearest[i]) for i in picked],dtype=int)
   elif mode=='county_any':donors=np.array([rng.choice(groups[counties[i]][groups[counties[i]]!=i]) for i in picked],dtype=int)
   else:
    donors=rng.integers(0,n-1,size=len(picked));donors+=donors>=picked
   Z=M.copy();Z[np.ix_(picked,struct)]=S[donors]
   cb=la.lstsq(Z,Y,lapack_driver='gelsy')[0];beta=float(cb[ic]);res=Y-Z@cb
   r2=1-(res@res)/(np.sum((Y-Y.mean())**2)); adj=1-(1-r2)*(n-1)/(n-Z.shape[1]);
   diff=float(np.mean(np.any(np.abs(S[picked]-S[donors])>1e-9,axis=1)))
   records.append({'mode':mode,'fraction_all_links':frac,'replicate':rep+1,'n_targeted':len(picked),'n_feature_bundles_different':round(diff*len(picked)),'beta_rate':beta,'attenuation_pct':100*(1-abs(beta/coefA)),'adjusted_r2':adj})
  print(mode,frac,'done',flush=True)
r=pd.DataFrame(records);r.to_csv(O/'broader_error_replicates.csv',index=False)
sumr=r.groupby(['mode','fraction_all_links']).agg(replicates=('beta_rate','size'),median_targeted=('n_targeted','median'),median_changed=('n_feature_bundles_different','median'),beta_median=('beta_rate','median'),beta_p025=('beta_rate',lambda x:x.quantile(.025)),beta_p975=('beta_rate',lambda x:x.quantile(.975)),attenuation_median=('attenuation_pct','median'),attenuation_p025=('attenuation_pct',lambda x:x.quantile(.025)),attenuation_p975=('attenuation_pct',lambda x:x.quantile(.975)),adj_r2_median=('adjusted_r2','median')).reset_index();sumr.to_csv(O/'broader_error_summary.csv',index=False)
pd.DataFrame([{'n':n,'beta_A':coefA,'beta_B':basebeta,'attenuation_pct':100*(1-abs(basebeta/coefA)),'min_donor_count_near':min(nearby_counts),'median_donor_count_near':np.median(nearby_counts),'county_groups':len(groups),'method':'Hypothetical donor swaps on all 4167 linked observations; not measured error rates or validated identities'}]).to_csv(O/'baseline_and_eligibility.csv',index=False)
print(sumr[['mode','fraction_all_links','beta_median','beta_p025','beta_p975','attenuation_median']].to_string(index=False),flush=True)
