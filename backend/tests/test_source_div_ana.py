import pytest
from unittest.mock import MagicMock
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'models'))
from source_diversity_analyzer import SourceDiversityAnalyzer
from fact import SourceType

def make_fact(source_type):
    fact = MagicMock()
    fact.source_type = source_type
    return fact

class TestSourceDiversityAnalyzer:

    def test_empty_analyzer_score_is_zero(self):
        analyzer = SourceDiversityAnalyzer()
        assert analyzer.calculate_diversity_score() == 0.0

    def test_single_source_type_is_biased(self):
        analyzer = SourceDiversityAnalyzer([
            make_fact(SourceType.NEWS),
            make_fact(SourceType.NEWS)
        ])
        assert analyzer.is_single_source_biased() == True

    def test_multiple_source_types_not_biased(self):
        analyzer = SourceDiversityAnalyzer([
            make_fact(SourceType.NEWS),
            make_fact(SourceType.ACADEMIC)
        ])
        assert analyzer.is_single_source_biased() == False

    def test_diversity_score_higher_with_more_types(self):
        single = SourceDiversityAnalyzer([
            make_fact(SourceType.NEWS),
            make_fact(SourceType.NEWS)
        ])
        diverse = SourceDiversityAnalyzer([
            make_fact(SourceType.NEWS),
            make_fact(SourceType.ACADEMIC)
        ])
        assert diverse.calculate_diversity_score() > single.calculate_diversity_score()

    def test_missing_source_types_returned(self):
        analyzer = SourceDiversityAnalyzer([make_fact(SourceType.NEWS)])
        missing = analyzer.get_missing_source_types()
        assert SourceType.NEWS.value not in missing

    def test_flag_low_diversity(self):
        analyzer = SourceDiversityAnalyzer([
            make_fact(SourceType.NEWS),
            make_fact(SourceType.NEWS)
        ])
        assert analyzer.flag_low_diversity() == True

    def test_compare_diversity(self):
        analyzer_a = SourceDiversityAnalyzer([make_fact(SourceType.NEWS)])
        analyzer_b = SourceDiversityAnalyzer([
            make_fact(SourceType.NEWS),
            make_fact(SourceType.ACADEMIC)
        ])
        result = analyzer_a.compare_diversity(analyzer_b)
        assert result['more_diverse'] == 'other'

    def test_generate_report_keys(self):
        analyzer = SourceDiversityAnalyzer([make_fact(SourceType.NEWS)])
        report = analyzer.generate_diversity_report()
        assert 'diversity_score' in report
        assert 'is_single_source_biased' in report
        assert 'recommendations' in report
        assert 'flagged_for_research' in report

    def test_add_fact(self):
        analyzer = SourceDiversityAnalyzer()
        analyzer.add_fact(make_fact(SourceType.NEWS))
        assert len(analyzer._facts) == 1

    def test_distribution_counts_correctly(self):
        analyzer = SourceDiversityAnalyzer([
            make_fact(SourceType.NEWS),
            make_fact(SourceType.NEWS),
            make_fact(SourceType.ACADEMIC)
        ])
        dist = analyzer.get_source_type_distribution()
        assert dist[SourceType.NEWS.value] == 2
        assert dist[SourceType.ACADEMIC.value] == 1