import pytest

from pkg_resources import Requirement as R

from pyp2rpm.dependency_parser import dependency_to_rpm


class TestDependencyParser():

    @pytest.mark.parametrize(('d', 'r', 'expected'), [
        ('docutils>=0.3,<1,!=0.5', True, [['Requires', 'docutils', '>=', '0.3'],
                                          ['Requires', 'docutils', '<', '1'],
                                          ['Conflicts', 'docutils', '=', '0.5']
                                          ]
         ),
        ('pytest>=0.3a5,<1.1.1.1,!=1', False, [['BuildRequires', 'pytest', '>=', '0.3a5'],
                                               ['BuildRequires', 'pytest', '<', '1.1.1.1'],
                                               ['BuildConflicts', 'pytest', '=', '1']
                                               ]
         ),

    ])
    def test_dependency_to_rpm(self, d, r, expected):
        # we can't convert lists of lists into sets => compare len and contents
        rpm_deps = dependency_to_rpm(R.parse(d), r)
        for dep in expected:
            assert dep in rpm_deps
        assert len(expected) == len(rpm_deps)
