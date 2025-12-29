from diving.util.translator import cleanup, translate


class TestTranslator:
    def test_load_yaml(self) -> None:
        assert translate('unguiculata') == 'Small-clawed'
        assert translate('acarnidae') == 'Non-thorny'

    def test_cleanup(self) -> None:
        assert cleanup('pilosa', 'Hairy') == 'Hairy'
        assert cleanup('polychaeta', 'Many bristled') == 'Many-bristled'
