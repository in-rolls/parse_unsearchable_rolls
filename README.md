## Parse Unsearchable Electoral Rolls

Some of the Indian electoral rolls are searchable, with a separate text layer in the right encoding (see [here](https://github.com/in-rolls/parse_elex_rolls)). Most are not. Here, we provide scripts that parse unsearchable rolls from the following states: Bihar, Chandigarh, Delhi (English), Haryana, Himachal Pradesh, Jharkhand, Madhya Pradesh, Rajasthan, Uttar Pradesh, and Uttarakhand.

### Scripts and Test Results from Sample of PDFs

We have a script for each state given the format for each state varies slightly. The python script takes as input path to specific pdf electoral rolls that need to be parsed and produces a CSV with the following columns generally---the precise set of columns varies by state:

```
number (top left box in the elector field), id, elector_name, father_or_husband_name,
husband (dummy for husband), house_no, age, sex, ac_name, parl_constituency, part_no,
year, state, filename, main_town, police_station, mandal, revenue_division, district,
pin_code, polling_station_name, polling_station_address, net_electors_male,
net_electors_female, net_electors_third_gender, net_electors_total
```

We do some basic checks for the quality of the data including checks on data types and missing values and the size of the field. For instance, data type check may look like numeric in numeric fields, and by size of the field, we mean, for example, number of characters in a name or in a pin_code.

1. [Assam](scripts/assam/)
2. [Bihar](scripts/bihar/)
3. [Chandigarh](scripts/chandigarh/)
4. [Dadra](scripts/dadra/)
5. [Daman](scripts/daman/)
6. [Delhi](scripts/delhi/)
7. [Haryana](scripts/haryana/)
8. [Himachal Pradesh](scripts/himachal/)
9. [Jharkhand](scripts/jharkhand/)
10. [Karnataka](scripts/karnataka/)
11. [Kerala](scripts/kerala/)
12. [Lakshadweep](scripts/lakshadweep/)
13. [Madhya Pradesh](scripts/madhya_pradesh/)
14. [Maharashtra](scripts/maharashtra/)
15. [Odisha](scripts/odisha/)
16. [Punjab](scripts/punjab/)
17. [Rajasthan](scripts/rajasthan/)
18. [Sikkim](scripts/sikkim/)
19. [Tamil Nadu](scripts/tamil_nadu/)
20. [Telangana](scripts/telangana/)
21. [Tripura](scripts/tripura/)
22. [Uttar Pradesh](scripts/uttar_pradesh/)
23. [Uttarakhand](scripts/uttarakhand/)
24. [West Bengal](scripts/west_bengal/)

### Data

The final data is posted [here](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/MUEGDT).

### Transliteration

We tried both [polyglot](https://pypi.org/project/polyglot/) and [indic_trans](https://github.com/libindic/indic-trans). Both have issues but indic_trans is better. [indicate](https://github.com/in-rolls/indicate) is yet better.

### Authors

Madhu Sanjeevi and Gaurav Sood

## 🔗 Adjacent Repositories

- [in-rolls/local_elections_bihar](https://github.com/in-rolls/local_elections_bihar) — Candidate Info. + Valid Votes Won by Cands. in the 2016 Bihar Panchayat Elections
- [in-rolls/local_elections_kerala](https://github.com/in-rolls/local_elections_kerala) — Kerala Local Government Seat Reservation Data and Winner Attributes
- [in-rolls/local_elections_up](https://github.com/in-rolls/local_elections_up) — UP Local Election Data --- GP and ULB. Seat reservation, winner, and candidates for some elections
- [in-rolls/local_elections_uttarakhand](https://github.com/in-rolls/local_elections_uttarakhand) — Data on Local Elections from Uttarakhand
- [in-rolls/ration_bihar](https://github.com/in-rolls/ration_bihar) — Scripts for scraping Ration Card Data From Bihar
