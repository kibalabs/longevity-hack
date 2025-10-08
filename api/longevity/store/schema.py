import sqlalchemy

# from sqlalchemy.dialects import postgresql as sqlalchemy_psql

# from longevity.store.entity_repository import EntityRepository

metadata = sqlalchemy.MetaData()

BigInt = sqlalchemy.Numeric(precision=78, scale=0)

# AssetsTable = sqlalchemy.Table(
#     'tbl_assets',
#     metadata,
#     sqlalchemy.Column(key='assetId', name='id', type_=sqlalchemy.Integer, autoincrement=True, primary_key=True, nullable=False),
#     sqlalchemy.Column(key='createdDate', name='created_date', type_=sqlalchemy.DateTime, nullable=False),
#     sqlalchemy.Column(key='updatedDate', name='updated_date', type_=sqlalchemy.DateTime, nullable=False),
#     sqlalchemy.Column(key='chainId', name='chain_id', type_=sqlalchemy.Integer, nullable=False),
#     sqlalchemy.Column(key='address', name='address', type_=sqlalchemy.Text, nullable=False),
#     sqlalchemy.Column(key='decimals', name='decimals', type_=sqlalchemy.Integer, nullable=False),
#     sqlalchemy.Column(key='name', name='name', type_=sqlalchemy.Text, nullable=False),
#     sqlalchemy.Column(key='symbol', name='symbol', type_=sqlalchemy.Text, nullable=False),
#     sqlalchemy.Column(key='logoUri', name='logo_uri', type_=sqlalchemy.Text, nullable=True),
#     sqlalchemy.Column(key='totalSupply', name='total_supply', type_=sqlalchemy.Numeric, nullable=False),
#     sqlalchemy.Column(key='isSpam', name='is_spam', type_=sqlalchemy.Boolean, nullable=False, server_default=sqlalchemy.text('false')),
#     sqlalchemy.UniqueConstraint('chainId', 'address', name='tbl_assets_ux_chain_id_address'),
# )

# AssetsRepository = EntityRepository(table=AssetsTable, modelClass=Asset)
