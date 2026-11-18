"""Reproduce a transaction-candidate audit for existing 4167 HMDA-SDAT links.
Only aggregate results are written; borrower/parcel identifiers are not redistributed.
The user-supplied sale file covers Aug-Dec 2025 despite a full-year where filter.
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__import__('os').environ.get('HMDA_SDAT_DATA_DIR', '.')).resolve()
OUT=ROOT/'MD_Property_Sales_Linkage_Audit'/'candidate_extension'
OUT.mkdir(parents=True,exist_ok=True)
a=pd.read_csv(ROOT/'Maryland_Property_Sales_2025.csv',dtype=str)
s=pd.read_csv(ROOT/'SDAT_2025_Market_Sales_With_Census_Tracts.csv',dtype=str)
i=pd.read_csv(ROOT/'HMDA_SDAT_final_analysis_ids.csv',dtype=str)
h=pd.read_csv(ROOT/'loan_purposes_1_state_MD(3).csv',dtype=str,low_memory=False)
# IDs were generated after the following original filtering, NOT source CSV row numbers
h=h.loc[(h.action_taken=='1') & pd.to_numeric(h.property_value,errors='coerce').notna()].reset_index(drop=True)
h['hmda_id']=(h.index+1).astype(str)
s['acct']=s['account_id_mdp_field_acctid'].str.strip()
a['acct']=a.ACCTID.str.strip()
l=i.merge(s,left_on='sdat_id',right_on='acct',validate='one_to_one').merge(h,on='hmda_id',validate='one_to_one')
assert len(l)==4167
l['date']=l['sales_segment_1_transfer_date_yyyy_mm_dd_mdp_field_tradate_sdat_field_89'].str.replace(r'\D','',regex=True).str[:8]
l['tract']=l.GEOID
l['price']=pd.to_numeric(l.sale_price_clean,errors='coerce')
l['hmda_midpoint']=pd.to_numeric(l.property_value,errors='coerce')
assert ((np.floor((l.price+2500)/5000)*5000)==l.hmda_midpoint).all()
assert (l.tract==l.census_tract).all()
a['price']=pd.to_numeric(a.CONSIDR1,errors='coerce')
a['rounded_price_5k']=np.floor((a.price+2500)/5000)*5000
assert len(a)==68484
assert (a.TRADATE.str[:6].isin(['202508','202509','202510','202511','202512'])).all()
# Exact account & event agreement, sale date is a stored snapshot field, not a proof of loan identity.
key_account_date=set(zip(a.acct,a.TRADATE))
key_three=set(zip(a.acct,a.TRADATE,a.price.fillna(-1)))
l['account_date']=[(x,d) in key_account_date for x,d in zip(l.sdat_id,l.date)]
l['account_date_price']=[(x,d,p if pd.notna(p) else -1) in key_three for x,d,p in zip(l.sdat_id,l.date,l.price)]
l['in_window']=l.date.between('20250801','20251231')
# One record per property account per tract+rounded consideration bin, avoiding double counting repeated deeds
valid=a.loc[a.CT2020.notna() & a.rounded_price_5k.notna() & a.acct.notna(),['CT2020','rounded_price_5k','acct']].drop_duplicates()
valid=valid.rename(columns={'CT2020':'tract','rounded_price_5k':'hmda_midpoint'})
# Group map for candidate accounts; existing source-linked account may or may not be among the candidates.
candidate_counts=valid.groupby(['tract','hmda_midpoint']).acct.nunique().rename('n_accounts').reset_index()
l=l.merge(candidate_counts,on=['tract','hmda_midpoint'],how='left',validate='many_to_one')
l['n_accounts']=l.n_accounts.fillna(0).astype(int)
original_presence=(valid.assign(present=True).rename(columns={'acct':'sdat_id'}))
l=l.merge(original_presence,on=['tract','hmda_midpoint','sdat_id'],how='left',validate='many_to_one')
l['original_present']=l.present.fillna(False).astype(bool)
l['n_competing_accounts']=l.n_accounts-l.original_present.astype(int)
assert (l.n_competing_accounts>=0).all()
# Dedup only conceptually: same account appears in repeated deed rows; count unique accounts, preserve all records.
metrics={
 'hmda_sdat_regression_pairs':len(l),
 'pairs_with_sdat_sale_date_aug_dec_2025':int(l.in_window.sum()),
 'pairs_with_sdat_sale_date_jan_jul_2025':int((~l.in_window).sum()),
 'pairs_with_account_date_in_external_sales':int(l.account_date.sum()),
 'pairs_with_account_date_consideration_in_external_sales':int(l.account_date_price.sum()),
 'aug_dec_pairs_with_account_date':int((l.in_window & l.account_date).sum()),
 'aug_dec_pairs_missing_account_date':int((l.in_window & ~l.account_date).sum()),
 'pairs_with_any_sales_account_same_tract_midpoint':int((l.n_accounts>0).sum()),
 'pairs_with_original_account_same_tract_midpoint':int(l.original_present.sum()),
 'pairs_with_one_or_more_competing_accounts':int((l.n_competing_accounts>0).sum()),
 'aug_dec_pairs_with_competing_accounts':int((l.in_window & (l.n_competing_accounts>0)).sum()),
 'account_date_pairs_with_competing_accounts':int((l.account_date & (l.n_competing_accounts>0)).sum()),
 'pairs_with_at_least_two_total_sales_accounts':int((l.n_accounts>=2).sum()),
 'pairs_with_zero_sales_accounts_same_tract_midpoint':int((l.n_accounts==0).sum()),
 'sales_tract_bin_distinct_sale_accounts':int(valid.acct.nunique()),
 'sale_rows_missing_consideration':int(a.price.isna().sum()),
 'sale_rows_missing_tract':int(a.CT2020.isna().sum()),
}
pd.DataFrame(metrics.items(),columns=['metric','value']).to_csv(OUT/'candidate_audit_summary.csv',index=False)
monthly=l.assign(month=l.date.str[:6]).groupby('month',sort=True).agg(
    regression_pairs=('hmda_id','size'),
    account_date_agreement=('account_date','sum'),
    same_tract_midpoint_candidate=('n_accounts',lambda x:(x>0).sum()),
    original_account_present=('original_present','sum'),
    pair_has_competing_account=('n_competing_accounts',lambda x:(x>0).sum()),
    pair_has_two_or_more_candidates=('n_accounts',lambda x:(x>=2).sum())
).reset_index()
monthly.to_csv(OUT/'linked_monthly_ambiguity.csv',index=False)
subset=l.assign(period=np.where(l.in_window,'Aug-Dec 2025','Jan-Jul 2025'))
by_period=subset.groupby('period',sort=True).agg(
 n_pairs=('hmda_id','size'),account_date=('account_date','sum'),
 original_account_in_sales_bin=('original_present','sum'),
 any_sales_account_in_bin=('n_accounts',lambda x:(x>0).sum()),
 competing_account=('n_competing_accounts',lambda x:(x>0).sum()),
 n_two_or_more_candidates=('n_accounts',lambda x:(x>=2).sum())
).reset_index()
by_period.to_csv(OUT/'linked_ambiguity_by_period.csv',index=False)
# Discrepancies: aggregate only; don't publish row-level IDs by default.
late=l[l.in_window].copy()
late['status']=np.select([late.account_date_price,late.account_date,late.original_present,late.n_accounts>0],['account-date-price agrees','account-date agrees; price missing/differs','original account only under tract+rounded value','other property candidate(s), original account not present'],default='no corresponding sale candidate')
late.status.value_counts().rename_axis('status').reset_index(name='n_pairs').to_csv(OUT/'late_year_coverage_categories.csv',index=False)
print('SUMMARY')
for k,v in metrics.items(): print(k,v)
print('PERIOD',by_period.to_string(index=False))
print('STATUS',late.status.value_counts().to_string())
