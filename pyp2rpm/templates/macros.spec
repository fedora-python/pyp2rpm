{# prints a single dependency for a specific python version #}
{%- macro one_dep(dep, python_version, epel=False) %}
{{ dep[0] }}:{{ ' ' * (15 - dep[0]|length) }}{{ dep[1]|name_for_python_version(python_version,
False, epel) }}{% if dep[2] is defined %} {{ dep[2] }} {{ dep[3] }}{% endif %}
{%- endmacro %}

{# Prints given deps (runtime or buildtime for given python_version,
   considering the base_python_version. #}
{# This cannot be implemented by macro for_python_versions because it needs to
   decide on its own, whether to even use the %if 0%{?with_pythonX} or not. #}
{%- macro dependencies(deps, runtime, python_version, base_python_version,
use_with=True, epel=False) %}
{%- if deps|length > 0 or not runtime %} {# for build deps, we always have at least 1 - pythonXX-devel #}
{%- if python_version != base_python_version and use_with %}
%if 0%{?with_python{{ python_version }}}
{%- endif %}
{%- for dep in deps -%}
{%- if python_version == base_python_version or not dep[1] == 'python-sphinx' -%}
{{ one_dep(dep, python_version, epel) }}
{%- endif -%}
{%- endfor %}
{%- if python_version != base_python_version and use_with %}
%endif # if with_python{{ python_version }}
{%- endif %}
{%- endif %}
{%- endmacro %}

{# For all python_versions, prints caller content. Content is surrounded by conditionals if
   python_version != base_python_version #}
{%- macro for_python_versions(python_versions, base_python_version) %}
{%- for pv in python_versions %}
{%- if pv != base_python_version %}
%if 0%{?with_python{{ pv }}}
{% endif %}
{{- caller(pv) }}
{%- if pv != base_python_version %}
%endif # with_python{{ pv }}
{% endif %}
{%- endfor %}
{%- endmacro %}

{% macro underscored_or_pypi(original, underscored) -%}
{% if underscored != original %}{{ underscored }}{% else %}%{pypi_name}{% endif %}
{%- endmacro %}
