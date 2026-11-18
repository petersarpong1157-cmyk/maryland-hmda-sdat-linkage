from pathlib import Path
import pandas as pd
import numpy as np
O=Path(__import__('os').environ.get('HMDA_SDAT_DATA_DIR', '.')).resolve()/'MD_Property_Sales_Linkage_Audit';O.mkdir(parents=True,exist_ok=True)
a=pd.read_csv(Path(__import__('os').environ.get('HMDA_SDAT_DATA_DIR', '.')).resolve()/'Maryland_Property_Sales_2025.csv',dtype=str)
b=pd.read_csv(Path(__import__('os').environ.get('HMDA_SDAT_DATA_DIR', '.')).resolve()/'SDAT_2025_Market_Sales_With_Census_Tracts.csv',dtype=str)
key='account_id_mdp_field_acctid'
b['ACCTID']=b[key].str.strip(); a['ACCTID']=a['ACCTID'].str.strip()
a['consideration']=pd.to_numeric(a['CONSIDR1'],errors='coerce'); b['sdat_consideration']=pd.to_numeric(b['sale_price_clean'],errors='coerce')
a['date_key']=a['TRADATE'];b['date_key']=b['sales_segment_1_transfer_date_yyyy_mm_dd_mdp_field_tradate_sdat_field_89'].str.replace(r'\D','',regex=True).str.slice(0,8)
print('SALES',len(a),'SDAT',len(b),'date range',a.date_key.min(),a.date_key.max())
print('unique IDs',a.ACCTID.nunique(),b.ACCTID.nunique())
print('sdat date',b.date_key.min(),b.date_key.max())
acc=a.ACCTID.isin(b.ACCTID)
print('account covered',int(acc.sum()),f'{acc.mean()*100:.2f}%','unique accounts',a.loc[acc,'ACCTID'].nunique())
print('dup sales account', int(a.ACCTID.duplicated().sum()),'SDAT duplicates',int(b.ACCTID.duplicated().sum()))
print('sales same acct same date duplicates',int(a.duplicated(['ACCTID','TRADATE']).sum()))
print('sales identical acct date consideration deed duplicates',int(a.duplicated(['ACCTID','TRADATE','CONSIDR1','DR1LIBER','DR1FOLIO']).sum()))
# keys for SDAT same account; count unique for account-date
b_keys=b[['ACCTID','date_key','sdat_consideration','GEOID']].copy()
m=a.merge(b_keys,on='ACCTID',how='left',indicator=True)
print('many to many expanded',len(m),'matched rows',len(m[m._merge=='both']))
# account-date matching based on distinct pairs, avoid cardinality overstatement
sdat_keys=set(zip(b.ACCTID,b.date_key)); a['same_account_date']=[(x,y) in sdat_keys for x,y in zip(a.ACCTID,a.date_key)]
combined_keys=set(zip(b.ACCTID,b.date_key,b.sdat_consideration.fillna(-1)));a['same_account_date_price']=[(x,y,z if pd.notna(z) else -1) in combined_keys for x,y,z in zip(a.ACCTID,a.date_key,a.consideration)]
print('account date match',int(a.same_account_date.sum()),'account date price match',int(a.same_account_date_price.sum()))
# tract concordance for any joined pair, only known
matched=m[m._merge=='both'].copy()
valid=matched.CT2020.notna() & matched.GEOID.notna()
print('tract concordance eligible',int(valid.sum()),'same tract',int((matched.loc[valid,'CT2020']==matched.loc[valid,'GEOID']).sum()))
print('sales null',a.isna().sum().to_dict())
# coverage by month
monthly=a.assign(month=a.date_key.str[:6]).groupby('month',as_index=False).agg(n_rows=('OBJECTID','size'),unique_accounts=('ACCTID','nunique'),with_consideration=('consideration','count'),account_in_SDAT=('ACCTID',lambda s:int(s.isin(b.ACCTID).sum())),same_account_date=('same_account_date','sum'),same_account_date_price=('same_account_date_price','sum'))
monthly.to_csv(O/'monthly_coverage.csv',index=False)
# account-level repetition counts for inspected contexts
rep=a.groupby('ACCTID').agg(n_rows=('OBJECTID','size'),n_dates=('TRADATE','nunique'),n_deeds=('DR1LIBER',lambda x:x.nunique())).reset_index()
print('repeat groups',rep.n_rows.value_counts().sort_index().head(14).to_dict())
print('accounts multiple dates',int((rep.n_dates>1).sum()))
print('positive consideration',int((a.consideration>0).sum()))
# audited indicators; don't publish account IDs by default
summary=[('property_sales_records',len(a)),('distinct_sale_accounts',a.ACCTID.nunique()),('sdat_records',len(b)),('distinct_sdat_accounts',b.ACCTID.nunique()),('sale_rows_with_sdat_account',int(acc.sum())),('unique_sale_accounts_in_sdat',a.loc[acc,'ACCTID'].nunique()),('sale_rows_matching_sdat_account_and_date',int(a.same_account_date.sum())),('sale_rows_matching_sdat_account_date_consideration',int(a.same_account_date_price.sum())),('sale_accounts_with_multiple_rows',int((rep.n_rows>1).sum())),('sale_accounts_with_multiple_transfer_dates',int((rep.n_dates>1).sum())),('duplicate_sale_account_date',int(a.duplicated(['ACCTID','TRADATE']).sum())),('missing_sales_tract',int(a.CT2020.isna().sum())),('missing_sales_consideration',int(a.consideration.isna().sum())),('sdat_join_known_tract_pairs',int(valid.sum())),('sdat_join_tract_agreements',int((matched.loc[valid,'CT2020']==matched.loc[valid,'GEOID']).sum()))]
pd.DataFrame(summary,columns=['metric','value']).to_csv(O/'account_linkage_audit_summary.csv',index=False)
print(monthly.to_string(index=False))
