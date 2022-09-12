try:
    import google.cloud.bigquery_storage as bq
    import pyarrow as pa
except ImportError:
    bq = None
    pa = None
from torch.utils.data import IterableDataset, IterDataPipe

class BigQueryPageLoaderIterDataPipe(IterDataPipe[pa.RecordBatch]):
    """
    Returns Arrow-encoded pages from the BigQuery
    """

    def __init__(self, project_id, dataset_id, table_name):
        super().__init__()
        self.client = bq.BigQueryReadClient()

        table = "projects/{}/datasets/{}/tables/{}".format(
            project_id, dataset_id, table_name
        )

        requested_session = bq.types.ReadSession()
        requested_session.table = table
        requested_session.data_format = bq.types.DataFormat.ARROW

        parent = "projects/{}".format(project_id)
        self.session = self.client.create_read_session(
            parent=parent,
            read_session=requested_session,
            max_stream_count=1,
        )
        self.reader = self.client.read_rows(self.session.streams[0].name)
        self.rows = self.reader.rows(self.session)
    
    def __iter__(self):
        for page in self.rows.pages:
            yield page.to_arrow()
    
    def __len__(self):
        raise TypeError(f"{type(self).__name__} instance doesn't have valid length")