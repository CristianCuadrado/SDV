"""Wrapper around CTGAN model."""

import rdt

from sdv.tabular.base import BaseTabularModel


class CTGAN(BaseTabularModel):
    """Model wrapping ``CTGANSynthesizer`` model.

    Args:
        field_names (list[str]):
            List of names of the fields that need to be modeled
            and included in the generated output data. Any additional
            fields found in the data will be ignored and will not be
            included in the generated output, except if they have
            been added as primary keys or fields to anonymize.
            If ``None``, all the fields found in the data are used.
        primary_key (str, list[str] or dict[str, dict]):
            Specification about which field or fields are the
            primary key of the table and information about how
            to generate them.
        field_types (dict[str, dict]):
            Dictinary specifying the data types and subtypes
            of the fields that will be modeled. Field types and subtypes
            combinations must be compatible with the SDV Metadata Schema.
        anonymize_fields (dict[str, str or tuple]):
            Dict specifying which fields to anonymize and what faker
            category they belong to. If arguments for the faker need to be
            passed to fine tune the value generation a tuple can be passed,
            where the first element is the category and the rest are additional
            positional arguments for the Faker.
        constraints (list[dict]):
            List of dicts specifying field and inter-field constraints.
            TODO: Format TBD
        table_metadata (dict or metadata.Table):
            Table metadata instance or dict representation.
            If given alongside any other metadata-related arguments, an
            exception will be raised.
            If not given at all, it will be built using the other
            arguments or learned from the data.
        epochs (int):
            Number of training epochs. Defaults to 300.
        log_frequency (boolean):
            Whether to use log frequency of categorical levels in conditional
            sampling. Defaults to ``True``.
        embedding_dim (int):
            Size of the random sample passed to the Generator. Defaults to 128.
        gen_dim (tuple or list of ints):
            Size of the output samples for each one of the Residuals. A Resiudal Layer
            will be created for each one of the values provided. Defaults to (256, 256).
        dis_dim (tuple or list of ints):
            Size of the output samples for each one of the Discriminator Layers. A Linear
            Layer will be created for each one of the values provided. Defaults to (256, 256).
        l2scale (float):
            Wheight Decay for the Adam Optimizer. Defaults to 1e-6.
        batch_size (int):
            Number of data samples to process in each step.
    """

    _CTGAN_CLASS = None
    _model = None

    HYPERPARAMETERS = {
        'TBD'
    }
    TRANSFORMER_TEMPLATES = {
        'O': rdt.transformers.LabelEncodingTransformer
    }

    def __init__(self, field_names=None, primary_key=None, field_types=None,
                 anonymize_fields=None, constraints=None, table_metadata=None,
                 epochs=300, log_frequency=True, embedding_dim=128, gen_dim=(256, 256),
                 dis_dim=(256, 256), l2scale=1e-6, batch_size=500):
        super().__init__(
            field_names=field_names,
            primary_key=primary_key,
            field_types=field_types,
            anonymize_fields=anonymize_fields,
            constraints=constraints,
            table_metadata=table_metadata
        )
        try:
            from ctgan import CTGANSynthesizer  # Lazy import to make dependency optional

            self._CTGAN_CLASS = CTGANSynthesizer
        except ImportError as ie:
            ie.msg += (
                '\n\nIt seems like `ctgan` is not installed.\n'
                'Please install it using:\n\n    pip install ctgan'
            )
            raise

        self._embedding_dim = embedding_dim
        self._gen_dim = gen_dim
        self._dis_dim = dis_dim
        self._l2scale = l2scale
        self._batch_size = batch_size
        self._epochs = epochs
        self._log_frequency = log_frequency

    def _fit(self, data):
        """Fit the model to the table.

        Args:
            data (pandas.DataFrame):
                Data to be learned.
        """
        self._model = self._CTGAN_CLASS(
            embedding_dim=self._embedding_dim,
            gen_dim=self._gen_dim,
            dis_dim=self._dis_dim,
            l2scale=self._l2scale,
            batch_size=self._batch_size,
        )
        categoricals = [
            field
            for field, meta in self._metadata.get_fields().items()
            if meta['type'] == 'categorical'
        ]
        self._model.fit(
            data,
            epochs=self._epochs,
            discrete_columns=categoricals,
            log_frequency=self._log_frequency,
        )

    def _sample(self, size):
        """Sample ``size`` rows from the model.

        Args:
            size (int):
                Amount of rows to sample.

        Returns:
            pandas.DataFrame:
                Sampled data.
        """
        return self._model.sample(size)
