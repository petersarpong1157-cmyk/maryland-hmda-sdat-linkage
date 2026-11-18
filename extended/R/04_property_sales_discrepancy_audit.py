from pathlib import Path
import pandas as pd, numpy as np
O=Path(__import__('os').environ.get('HMDA_SDAT_DATA_DIR', '.')).resolve()/'MD_Property_Sales_Linkage_Audit';O.mkdir(parents=True,exist_ok=True)
a=pd.read_csv(Path(__import__('os').environ.get('HMDA_SDAT_DATA_DIR', '.')).resolve()/'Maryland_Property_Sales_2025.csv',dtype=str).fillna('')
b=pd.read_csv(Path(__import__('os').environ.get('HMDA_SDAT_DATA_DIR', '.')).resolve()/'SDAT_2025_Market_Sales_With_Census_Tracts.csv',dtype=str).fillna('')
b['ACCTID']=b['account_id_mdp_field_acctid'].str.strip(); a['ACCTID']=a['ACCTID'].str.strip()
b['date']=b['sales_segment_1_transfer_date_yyyy_mm_dd_mdp_field_tradate_sdat_field_89'].str.replace(r'\D','',regex=True).str.slice(0,8); a['date']=a['TRADATE']
a['consideration']=pd.to_numeric(a.CONSIDR1,errors='coerce');b['consideration']=pd.to_numeric(b.sale_price_clean,errors='coerce')
# Produce one-to-one matching for unique SDAT account records; distinguish account and date agreement from ambiguous repeats
b_unique=b.drop_duplicates(['ACCTID','date','consideration','GEOID'])[['ACCTID','date','consideration','GEOID']]
m=a.merge(b_unique,on='ACCTID',suffixes=('_sales','_sdat'),how='inner')
conflict=m[(m.CT2020!='') & (m.GEOID!='') & (m.CT2020!=m.GEOID)]
print('cross pairs',len(m),'tract conflicts rows',len(conflict),'unique sales OIDs',conflict.OBJECTID.nunique(),'unique accounts',conflict.ACCTID.nunique())
print('conflict same date',int((conflict.date_sales==conflict.date_sdat).sum()))
# key comparisons exact account + date, avoid cross-product of several temporal transactions
md=a.merge(b_unique,on=['ACCTID','date'],how='inner',suffixes=('_sales','_sdat'))
print('exact acct date pairs',len(md),'sale OIDs',md.OBJECTID.nunique())
known=md.consideration_sales.notna() & md.consideration_sdat.notna()
mis=md[known & (md.consideration_sales!=md.consideration_sdat)].copy()
print('known price comparisons',known.sum(),'mismatch pairs',len(mis),'unique sale OIDs',mis.OBJECTID.nunique())
print('mismatch abs delta', (mis.consideration_sales-mis.consideration_sdat).abs().describe().to_dict())
print('deed repeated across accounts',a.groupby(['DR1LIBER','DR1FOLIO']).ACCTID.nunique().sort_values(ascending=False).head(8).to_dict())
repeats=a.groupby(['ACCTID','TRADATE'],dropna=False).agg(rows=('OBJECTID','size'),deeds=('DR1LIBER','nunique'),consideration_values=('CONSIDR1','nunique')).reset_index()
print('repeat acct-date groups',int((repeats.rows>1).sum()),'with multiple consideration',int(((repeats.rows>1)&(repeats.consideration_values>1)).sum()))
print('sample date mismatch',conflict[['CT2020','GEOID','date_sales','date_sdat']].head(6).to_string(index=False))
# aggregate summaries without parcel/account IDs to be safe
rows=[('sales_records',len(a)),('sdat_records',len(b)),('cross_join_account_pairs',len(m)),('cross_join_tract_conflicts',len(conflict)),('cross_join_tract_conflict_unique_sales',conflict.OBJECTID.nunique()),('cross_join_tract_conflict_unique_accounts',conflict.ACCTID.nunique()),('cross_join_tract_conflicts_with_same_transfer_date',int((conflict.date_sales==conflict.date_sdat).sum())),('account_date_pairs',len(md)),('account_date_unique_sales',md.OBJECTID.nunique()),('account_date_both_considerations_observed_pairs',int(known.sum())),('account_date_mismatched_price_pairs',len(mis)),('account_date_mismatched_price_unique_sales',mis.OBJECTID.nunique()),('repeated_account_date_groups',int((repeats.rows>1).sum())),('repeated_account_date_groups_with_multiple_values',int(((repeats.rows>1)&(repeats.consideration_values>1)).sum()))]
pd.DataFrame(rows,columns=['metric','value']).to_csv(O/'deep_audit_summary.csv',index=False)
# tract conflicts only nonidentifying county FIPS level
conflict.assign(sales_county=conflict.CT2020.str[:5],sdat_county=conflict.GEOID.str[:5],same_date=(conflict.date_sales==conflict.date_sdat)).groupby(['sales_county','sdat_county','same_date']).size().rename('pair_count').reset_index().to_csv(O/'tract_disagreement_aggregate.csv',index=False)
# price discrepancies histogram
mis.assign(delta=(mis.consideration_sales-mis.consideration_sdat).abs(),band=lambda t:pd.cut(t.delta,[-1,1,100,1000,5000,10000,50000,np.inf],labels=['0-1','2-100','101-1k','1k-5k','5k-10k','10k-50k','>50k'])).groupby('band',observed=True).size().rename('pair_count').reset_index().to_csv(O/'price_disagreement_bands.csv',index=False)
