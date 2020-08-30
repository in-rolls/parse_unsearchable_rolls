### Parse Bihar Electoral Rolls

We parse [Bihar electoral rolls](https://github.com/in-rolls/electoral_rolls). (For scripts for parsing 'readable' electoral rolls, see [here](https://github.com/in-rolls/parse_elex_rolls)

The [python notebook](scripts/parse_bihar_hindi.ipynb) can be used to process Bihar Hindi pdf electoral rolls for 2015/17/20. It produces a CSV with the following columns:

```
number (top left box in the elector field), id, elector_name, father_or_husband_name, husband (dummy for husband), house_no, age, sex, ac_name, parl_constituency, part_no, year, state, filename, main_town, police_station, mandal, revenue_division, district, pin_code, polling_station_name, polling_station_address, net_electors_male, net_electors_female, net_electors_third_gender, net_electors_total, original_or_amendment, last_1st_male, last_1st_female , last_1st_third, last_1st_total, last_2nd_male, last_2nd_female, last_2nd_third, last_2nd_total, last_3rd_male, last_3rd_female, last_3rd_third, last_3rd_total
```

The test results for a select few rolls are [here](final_csv_test_report.ipynb)

### Data

The final data for Bihar electoral rolls is posted [here](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/MUEGDT).

### Transliteration

For transliteration, we tried both [polyglot](https://pypi.org/project/polyglot/) and [indic_trans](https://github.com/libindic/indic-trans). Both have issues but indic_trans is better.

### Authors

Madhu Sanjeevi and Gaurav Sood
