# Gate 1: identity check

Date: 2026-11-05. Sample: 50 of 596 players whose only identity evidence is an exact name match (status `name`), drawn with a fixed seed.

**Method:** for each match, `tools/gate1_identity_check.py` fetched the matched person's Portuguese or English Wikipedia article and checked whether it names a club the dataset has the player at. Rows where it doesn't were judged by hand from birth year, Wikidata clubs and the article text.

## Result
| Verdict | Count |
|---|---|
| Correct (article names the club) | 32 |
| Wrong | 4 |
| Unproven (plausible, not confirmed) | 14 |

Proven correct: 32 of 50 (64%), below the 90% the spec requires.

**Decision:** name-only matches do not keep a fame-based tier; they get the default Raiz tier (`NAME_ONLY_TRUSTED = False` in `generator/config.py`).

**Pattern in the errors:** every wrong match is an older player with the same nickname (born 1966–1980). Rejecting candidates whose age in the dataset season is implausible would remove this class; it needs birth dates in the Wikidata fetch.

## Rows
| Dataset name | Dataset clubs | Matched | Verdict | Reason | Source |
|---|---|---|---|---|---|
| Thomazella | Mirassol 2025–2026 | Q115574561 Thomazella | **correct** | article names Mirassol | [source](https://en.wikipedia.org/wiki/Thomazella) |
| Filipe Machado | Chapecoense 2016 | Q978679 Filipe José Machado | **correct** | article names Chapecoense | [source](https://pt.wikipedia.org/wiki/Filipe_Machado) |
| Jean Patrick Reis | Ponte Preta 2017 | Q21552771 Jean Patrick Reis | **unproven** | exact full name, born 1992; article doesn't name Ponte Preta | [source](https://en.wikipedia.org/wiki/Jean_Patrick) |
| Gustavo Sauer | Botafogo 2022–2023 | Q23994916 Gustavo Sauer | **unproven** | born 1993, winger; article and Wikidata stop before 2022 | [source](https://en.wikipedia.org/wiki/Gustavo_Sauer) |
| Ebert Willian Amâncio | Avaí 2017–2019 | Q717218 Ebert Willian Amâncio | **correct** | article names Avaí | [source](https://pt.wikipedia.org/wiki/Ebert_Willian_Am%C3%A2ncio) |
| Nahuel Bustos | São Paulo 2022 | Q23679896 Nahuel Bustos | **correct** | article names São Paulo | [source](https://pt.wikipedia.org/wiki/Nahuel_Bustos) |
| Matheus Salustiano | Vitória 2014 | Q28648824 Matheus Salustiano | **unproven** | exact name, born 1993; article doesn't name Vitória | [source](https://en.wikipedia.org/wiki/Matheus_Salustiano) |
| Felipe Pires | Fortaleza, Juventude 2019–2022 | Q19279527 Felipe Pires | **correct** | article names Fortaleza | [source](https://pt.wikipedia.org/wiki/Felipe_Pires) |
| Giovanni Manson Ribeiro | Fluminense 2023 | Q98970158 Giovanni | **correct** | article names Fluminense | [source](https://en.wikipedia.org/wiki/Giovanni_%28footballer%2C_born_2002%29) |
| Fernando Viana | Joinville 2015 | Q28377758 Fernando Viana | **correct** | article names Joinville | [source](https://pt.wikipedia.org/wiki/Fernando_Viana_%28futebolista%29) |
| Ricardo de Souza Silva | Figueirense 2015 | Q1185618 Ricardo Souza Silva | **wrong** | matched Ricardinho, born 1975, would be 39 at Figueirense in 2015 | [source](https://en.wikipedia.org/wiki/Ricardinho_%28footballer%2C_born_1975%29) |
| João Magno | Goiás 2023 | Q120493368 João Magno | **correct** | article names Goiás | [source](https://en.wikipedia.org/wiki/Jo%C3%A3o_Magno) |
| Jonathas Cristian de Jesus | Corinthians 2018 | Q2689047 Jonatas Cristian de Jesus | **correct** | article names Corinthians | [source](https://pt.wikipedia.org/wiki/Jonathas_Cristian_de_Jesus) |
| Lepu | Vitória 2024 | Q59205846 Willean Bernardo Willemen | **unproven** | matched by alias, born 1997; no article | no article |
| Moacir Costa da Silva | Atlético-GO 2020 | Q6886339 Moacir Costa da Silva | **correct** | article names Atlético-GO | [source](https://en.wikipedia.org/wiki/Moacir_%28footballer%2C_born_1986%29) |
| Luciano Giménez | Cuiabá 2024 | Q122947851 Luciano Giménez | **correct** | article names Cuiabá | [source](https://en.wikipedia.org/wiki/Luciano_Gim%C3%A9nez) |
| Emerson Rodríguez | Vasco 2024 | Q102347078 Emerson Rodríguez | **correct** | article names Vasco | [source](https://en.wikipedia.org/wiki/Emerson_Rodr%C3%ADguez_%28footballer%29) |
| Jucimar José Teixeira | Botafogo 2016 | Q27825281 Jucimar José Teixeira | **correct** | article names Botafogo | [source](https://en.wikipedia.org/wiki/Alem%C3%A3o_%28footballer%2C_born_May_1990%29) |
| Adalberto dos Santos Rodrigues | América-MG, Fortaleza 2016–2019 | Q67076090 Adalberto | **unproven** | born 1987; no article | no article |
| Patrick de Lucca | Bahia 2021 | Q105888160 Patrick de Lucca | **correct** | article names Bahia | [source](https://en.wikipedia.org/wiki/Patrick_de_Lucca) |
| Helibelton Palacios | Cruzeiro 2023 | Q5893752 Helibelton Palacios | **correct** | article names Cruzeiro | [source](https://en.wikipedia.org/wiki/Helibelton_Palacios) |
| Bruno Henrique Marques Torres | Santos 2020 | Q102428673 Bruno Henrique Marques Torres | **correct** | article names Santos | [source](https://en.wikipedia.org/wiki/Bruno_Marques) |
| Betinho | Sport 2020–2021 | Q888001 Gilberto Carlos Nascimento | **wrong** | matched a player born 1966; dataset Betinho played for Sport in 2020–2021 | [source](https://en.wikipedia.org/wiki/Betinho_%28footballer%2C_born_1966%29) |
| Tobias Figueiredo | Criciúma 2024 | Q7811626 Tobias Figueiredo | **correct** | article names Criciúma | [source](https://pt.wikipedia.org/wiki/Tobias_Figueiredo) |
| Valentín Depietri | Fortaleza 2021 | Q104649871 Valentín Depietri | **correct** | article names Fortaleza | [source](https://en.wikipedia.org/wiki/Valent%C3%ADn_Depietri) |
| Gustavo Nunes | Grêmio 2024 | Q125179502 Gustavo Nunes | **correct** | article names Grêmio | [source](https://pt.wikipedia.org/wiki/Gustavo_Nunes) |
| Matheus Jussa | Cruzeiro, Fortaleza, Internacional 2020–2023 | Q18637712 Matheus Jussa | **correct** | article names Cruzeiro, Fortaleza, Internacional | [source](https://pt.wikipedia.org/wiki/Matheus_Jussa) |
| Fabiano da Silva Souza | Vitória 2018 | Q28510282 Fabiano da Silva Souza | **correct** | article names Vitória | [source](https://en.wikipedia.org/wiki/Fabiano_%28footballer%2C_born_1990%29) |
| Magno Jose da Silva | Atlético-GO, Goiás 2022–2024 | Q60685378 Magno Jose da Silva | **correct** | article names Goiás | [source](https://en.wikipedia.org/wiki/Maguinho) |
| Vinícius Paiva | Vasco 2020 | Q94759948 Vinícius Paiva | **unproven** | exact name, born 2001; article doesn't name Vasco | [source](https://en.wikipedia.org/wiki/Vin%C3%ADcius_Paiva) |
| Jael | Ceará, Grêmio 2017–2021 | Q6121721 Jael | **correct** | article names Grêmio | [source](https://pt.wikipedia.org/wiki/Jael_%28futebolista%29) |
| Bochecha | Botafogo 2018–2019 | Q55315017 Bochecha | **unproven** | born 1996; no article | no article |
| Kelvin Osorio | Cuiabá 2022 | Q24579391 Kelvin Osorio | **unproven** | born 1993, Colombian midfielder; article doesn't reach 2022 | [source](https://en.wikipedia.org/wiki/Kelvin_Osorio) |
| Yuri César | Fortaleza 2020 | Q84314152 Yuri César | **correct** | article names Fortaleza | [source](https://en.wikipedia.org/wiki/Yuri_C%C3%A9sar) |
| Henrique Mattos | Sport 2014 | Q28777377 Henrique Mattos | **unproven** | born 1990, defender; article doesn't name Sport | [source](https://en.wikipedia.org/wiki/Henrique_Mattos) |
| Dentinho | Avaí 2022 | Q514577 Dentinho | **unproven** | born 1989, forward; article doesn't name Avaí | [source](https://en.wikipedia.org/wiki/Dentinho) |
| Tomas Almino da Silva Bastos | Coritiba 2017 | Q18612401 Tomas Almino da Silva Bastos | **unproven** | exact full name, born 1992; article doesn't name Coritiba | [source](https://en.wikipedia.org/wiki/Tomas_Bastos) |
| Marquinho | Fluminense 2016–2017 | Q655449 Marco Antônio dos Santos | **wrong** | matched a player born 1966; dataset Marquinho played for Fluminense in 2016–2017 | [source](https://en.wikipedia.org/wiki/Marquinho_%28footballer%2C_born_1966%29) |
| Rafael Elias | Cruzeiro, Cuiabá, Goiás 2019–2024 | Q55081250 Rafael Elias | **correct** | article names Cruzeiro | [source](https://en.wikipedia.org/wiki/Rafael_Elias) |
| Reynaldo Cesar Moraes | Coritiba, Goiás, Vitória 2022–2024 | Q29349155 Reynaldo Cesar Moraes | **unproven** | exact full name, born 1997, centre-back; article doesn't name the clubs | [source](https://en.wikipedia.org/wiki/Reynaldo_%28footballer%2C_born_1997%29) |
| Robson Reis | Santos 2021 | Q105722901 Robson Reis | **correct** | article names Santos | [source](https://en.wikipedia.org/wiki/Robson_Reis) |
| Paulo Vitor Fernandes Pereira | Vasco 2017 | Q30087944 Paulo Vitor Fernandes Pereira | **correct** | article names Vasco | [source](https://en.wikipedia.org/wiki/Paulo_Vitor_%28footballer%2C_born_1999%29) |
| Rodrigo Biro | Chapecoense 2014 | Q26829248 Rodrigo Biro | **unproven** | born 1986, left back; article doesn't name Chapecoense | [source](https://en.wikipedia.org/wiki/Rodrigo_Biro) |
| Kaiky Fernandes | Santos 2021 | Q105722883 Kaiky Fernandes | **correct** | article names Santos | [source](https://pt.wikipedia.org/wiki/Kaiky) |
| Gilberto dos Santos Souza Júnior | Goiás 2019 | Q15831024 Gilberto dos Santos Souza Júnior | **unproven** | exact full name, born 1988; article doesn't name Goiás | [source](https://en.wikipedia.org/wiki/Gilberto_%28footballer%2C_born_1988%29) |
| Juan Manuel Salgueiro | Botafogo 2016 | Q2560292 Juan Manuel Salgueiro | **correct** | article names Botafogo | [source](https://pt.wikipedia.org/wiki/Juan_Manuel_Salgueiro) |
| Xavier | Corinthians 2020–2022 | Q6294230 José Xavier Costa | **wrong** | matched José Xavier Costa, born 1980; dataset Xavier played for Corinthians in 2020–2022 | no article |
| Douglas Silva Bacelar | Chapecoense 2017–2019 | Q3934983 Douglas Silva Bacelar | **correct** | article names Chapecoense | [source](https://pt.wikipedia.org/wiki/Douglas_Silva_Bacelar) |
| Henrique Lordelo | Goiás 2020–2022 | Q104415836 Henrique Lordelo | **correct** | article names Goiás | [source](https://en.wikipedia.org/wiki/Henrique_Lordelo) |
| Leandro Vilela | Paraná 2018 | Q48864777 Leandro Vilela | **correct** | article names Paraná | [source](https://en.wikipedia.org/wiki/Leandro_Vilela) |
