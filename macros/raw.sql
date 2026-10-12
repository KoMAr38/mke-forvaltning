{# Leser en rå CSV fra data/raw/ssb med alle kolonner som tekst. #}
{% macro raw(fil) -%}
read_csv('{{ var("raw_mappe") }}/{{ fil }}.csv', header = true, all_varchar = true)
{%- endmacro %}
