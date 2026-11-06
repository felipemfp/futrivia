# Fact check (T16)

Date: 2026-11-05. Sample: 20 prompts drawn with a fixed seed from an 86-day build, and 3 answers each (most obvious, middle, rarest): 60 answers.

**Method:** `tools/fact_check.py` checks whether each player's Portuguese or English Wikipedia article names the club in the answer's evidence. That confirms the player and club, not the exact stat. The 10 answers it couldn't confirm were checked against match reports by web search.

## Result
| Verdict | Count |
|---|---|
| Correct | 58 |
| Wrong | 1 |
| Unproven | 1 |

58 of 60 correct (97%), above the 90% the spec requires. The one error came from the source data, a red card filed against the wrong player. It is excluded through `data/exclusions.csv`, with a test.

**Limit of the method:** the automatic check confirms player and club, not each stat. Each of the 9 stats checked against match reports matched except the one error, which is the main evidence on stat accuracy.

**Display issue found:** several answers show legal names (e.g. "Carlos Eduardo Antônio dos Santos" for Kadu, "Maicon Douglas Sisenando"). Fixed by preferring the Portuguese Wikipedia article title as the shown name.

## Rows
| Prompt | Answer | Tier | Evidence | Verdict | Check |
|---|---|---|---|---|---|
| `expulso-juventude-2020-2026` | Nenê | arquibancada | Juventude 2024 | **correct** | player's article names Juventude ([source](https://pt.wikipedia.org/wiki/Nen%C3%AA_%28futebolista%29)) |
| `expulso-juventude-2020-2026` | Lucas Barbosa | raiz | Juventude 2024 | **wrong** | Corinthians 1×1 Juventude, 4 Aug 2024: Barbosa scored at 82'; goalkeeper Gabriel was sent off ([Gazeta Esportiva](https://www.gazetaesportiva.com/times/corinthians/com-dois-a-mais-corinthians-empata-com-juventude-na-arena-e-volta-para-o-z4-do-brasileiro/)). Fixed: the source row is in `data/exclusions.csv`. |
| `expulso-juventude-2020-2026` | Hudson | enciclopedia | Juventude 2025 | **correct** | player's article names Juventude ([source](https://en.wikipedia.org/wiki/Hudson_%28footballer%2C_born_2001%29)) |
| `marcou-por-bragantino-2026` | Isidro Pitta | arquibancada | Bragantino 2026 | **correct** | player's article names Bragantino ([source](https://pt.wikipedia.org/wiki/Isidro_Pitta)) |
| `marcou-por-bragantino-2026` | Juninho Capixaba | raiz | Bragantino 2026 | **correct** | player's article names Bragantino ([source](https://pt.wikipedia.org/wiki/Juninho_Capixaba)) |
| `marcou-por-bragantino-2026` | Lucas Barbosa | enciclopedia | Bragantino 2026 | **correct** | player's article names Bragantino ([source](https://en.wikipedia.org/wiki/Lucas_Barbosa_%28footballer%2C_born_2001%29)) |
| `expulso-figueirense-2014-2019` | Gatito Fernández | arquibancada | Figueirense 2016 | **correct** | player's article names Figueirense ([source](https://pt.wikipedia.org/wiki/Gatito_Fern%C3%A1ndez)) |
| `expulso-figueirense-2014-2019` | França | raiz | Figueirense 2014 | **correct** | sent off in Figueirense 1×2 Internacional, 6 Dec 2014 ([Sul21](https://sul21.com.br/noticias-em-geral/2014/12/gol-aos-50-minutos-garante-o-inter-no-terceiro-lugar-2/)) |
| `expulso-figueirense-2014-2019` | Yago Rocha | enciclopedia | Figueirense 2016 | **correct** | sent off in Figueirense 1×1 Atlético-MG, 3 Jul 2016 ([Gazeta Esportiva](https://www.gazetaesportiva.com/?p=2333704)) |
| `marcou-por-america-mg-2023` | Wellington Paulista | arquibancada | América-MG 2023 | **correct** | player's article names América-MG ([source](https://pt.wikipedia.org/wiki/Wellington_Paulista)) |
| `marcou-por-america-mg-2023` | Emmanuel Martínez | raiz | América-MG 2023 | **correct** | one goal for América-MG in 2023 per season reports; the match isn't identified ([FBref](https://aws.fbref.com/en/players/74758396/matchlogs/2023/c24/gca/Leandro-Emmanuel-Martinez-Match-Logs)) |
| `marcou-por-america-mg-2023` | Everaldo Silva do Nascimento | enciclopedia | América-MG 2023 | **correct** | player's article names América-MG ([source](https://en.wikipedia.org/wiki/Everaldo_%28footballer%2C_born_1994%29)) |
| `expulso-corinthians-2014-2019` | Paolo Guerrero | arquibancada | Corinthians 2014 | **correct** | player's article names Corinthians ([source](https://pt.wikipedia.org/wiki/Paolo_Guerrero)) |
| `expulso-corinthians-2014-2019` | Leonardo Peixoto Príncipe | raiz | Corinthians 2016 | **correct** | player's article names Corinthians ([source](https://en.wikipedia.org/wiki/L%C3%A9o_Pr%C3%ADncipe)) |
| `expulso-corinthians-2014-2019` | Yago Fernando da Silva | enciclopedia | Corinthians 2016 | **correct** | player's article names Corinthians ([source](https://pt.wikipedia.org/wiki/Yago_Fernando_da_Silva)) |
| `marcou-contra-internacional-2026` | Neymar | arquibancada | Santos 2026 | **correct** | player's article names Santos ([source](https://pt.wikipedia.org/wiki/Neymar)) |
| `marcou-contra-internacional-2026` | Stiven Mendoza | raiz | Athletico-PR 2026 | **correct** | player's article names Athletico-PR ([source](https://pt.wikipedia.org/wiki/Stiven_Mendoza)) |
| `marcou-contra-internacional-2026` | Diego Tarzia | enciclopedia | Vitória 2026 | **correct** | scored at 90+7 in Vitória 2×0 Internacional, 23 May 2026 ([ESPN](https://www.espn.co.uk/football/match/_/gameId/401841130)) |
| `expulso-joinville-2014-2026` | Edson Ratinho | arquibancada | Joinville 2015 | **correct** | player's article names Joinville ([source](https://en.wikipedia.org/wiki/Edson_Ratinho)) |
| `expulso-joinville-2014-2026` | Alef Vieira Santos | raiz | Joinville 2015 | **correct** | player's article names Joinville ([source](https://en.wikipedia.org/wiki/Alef_%28footballer%2C_born_1993%29)) |
| `expulso-joinville-2014-2026` | Carlos Eduardo Antônio dos Santos | resenha | Joinville 2015 | **correct** | the red card in Joinville 1×0 Figueirense, 17 Oct 2015, went to Kadu, the usual nickname of Carlos Eduardo ([Gazeta Esportiva](https://www.gazetaesportiva.com/?p=2112109)); identity by nickname, not by name |
| `marcou-por-cuiaba-2024` | Deyverson | arquibancada | Cuiabá 2024 | **correct** | player's article names Cuiabá ([source](https://pt.wikipedia.org/wiki/Deyverson)) |
| `marcou-por-cuiaba-2024` | Bruno Alves | raiz | Cuiabá 2024 | **correct** | scored in Cuiabá v São Paulo, 5 Oct 2024 ([ESPN](https://africa.espn.com/football/match/_/gameId/699635/sao-paulo-cuiaba)) |
| `marcou-por-cuiaba-2024` | Matheus Alexandre | enciclopedia | Cuiabá 2024 | **correct** | player's article names Cuiabá ([source](https://en.wikipedia.org/wiki/Matheus_Alexandre)) |
| `gols-por-fortaleza-10` | Thiago Galhardo | arquibancada | Fortaleza 2022, Fortaleza 2023 | **correct** | player's article names Fortaleza, Fortaleza ([source](https://pt.wikipedia.org/wiki/Thiago_Galhardo)) |
| `gols-por-fortaleza-10` | Wellington Paulista | raiz | Fortaleza 2019, Fortaleza 2020, Fortaleza 2021 | **correct** | player's article names Fortaleza, Fortaleza, Fortaleza ([source](https://pt.wikipedia.org/wiki/Wellington_Paulista)) |
| `gols-por-fortaleza-10` | Moisés | enciclopedia | Fortaleza 2022, Fortaleza 2023, Fortaleza 2024 | **correct** | player's article names Fortaleza, Fortaleza, Fortaleza ([source](https://en.wikipedia.org/wiki/Mois%C3%A9s_%28footballer%2C_born_1996%29)) |
| `marcou-por-bahia-e-cruzeiro` | Everton Ribeiro | arquibancada | Cruzeiro 2014, Bahia 2024 | **correct** | player's article names Cruzeiro, Bahia ([source](https://pt.wikipedia.org/wiki/%C3%89verton_Ribeiro)) |
| `marcou-por-bahia-e-cruzeiro` | Gilberto | raiz | Bahia 2018, Bahia 2019, Bahia 2020 e mais 2 | **correct** | player's article names Bahia, Bahia, Bahia ([source](https://pt.wikipedia.org/wiki/Gilberto_Oliveira_Souza_J%C3%BAnior)) |
| `marcou-por-bahia-e-cruzeiro` | Élber | enciclopedia | Cruzeiro 2016, Cruzeiro 2017, Bahia 2018 e mais 2 | **correct** | player's article names Cruzeiro, Cruzeiro, Bahia ([source](https://pt.wikipedia.org/wiki/%C3%89lber_%28futebolista%29)) |
| `acrescimos-chapecoense` | Túlio de Melo | arquibancada | Chapecoense 2017 | **correct** | player's article names Chapecoense ([source](https://pt.wikipedia.org/wiki/T%C3%BAlio_de_Melo)) |
| `acrescimos-chapecoense` | Leandro | raiz | Chapecoense 2014, Chapecoense 2018 | **unproven** | dataset name 'Leandro' covers several players; the stoppage-time goal isn't confirmed by an outside source |
| `acrescimos-chapecoense` | Elicarlos | enciclopedia | Chapecoense 2018 | **correct** | player's article names Chapecoense ([source](https://pt.wikipedia.org/wiki/Elicarlos)) |
| `marcou-por-gremio-2020` | Maicon Douglas Sisenando | arquibancada | Grêmio 2020 | **correct** | player's article names Grêmio ([source](https://pt.wikipedia.org/wiki/Maicon_Douglas_Sisenando)) |
| `marcou-por-gremio-2020` | César Pinares | raiz | Grêmio 2020 | **correct** | player's article names Grêmio ([source](https://pt.wikipedia.org/wiki/C%C3%A9sar_Pinares)) |
| `marcou-por-gremio-2020` | Luiz Fernando | enciclopedia | Grêmio 2020 | **correct** | player's article names Grêmio ([source](https://pt.wikipedia.org/wiki/Luiz_Fernando_Moraes_dos_Santos)) |
| `titular-bragantino-2026-1` | Matheus Fernandes | arquibancada | Bragantino 2026 | **correct** | player's article names Bragantino ([source](https://pt.wikipedia.org/wiki/Matheus_Fernandes_%28futebolista%29)) |
| `titular-bragantino-2026-1` | Fabinho | raiz | Bragantino 2026 | **correct** | player's article names Bragantino ([source](https://pt.wikipedia.org/wiki/Fabinho_%28futebolista%2C_2002%29)) |
| `titular-bragantino-2026-1` | Cauê Nascimento | enciclopedia | Bragantino 2026 | **correct** | player's article names Bragantino ([source](https://en.wikipedia.org/wiki/Cau%C3%AA_%28footballer%2C_born_2006%29)) |
| `marcou-contra-santos-2019` | Daniel Alves | arquibancada | São Paulo 2019 | **correct** | player's article names São Paulo ([source](https://pt.wikipedia.org/wiki/Daniel_Alves)) |
| `marcou-contra-santos-2019` | Braian Ezequiel Romero | raiz | Athletico-PR 2019 | **correct** | player's article names Athletico-PR ([source](https://pt.wikipedia.org/wiki/Braian_Romero)) |
| `marcou-contra-santos-2019` | João Paulo da Silva Alves | enciclopedia | Avaí 2019 | **correct** | player's article names Avaí ([source](https://en.wikipedia.org/wiki/Jo%C3%A3o_Paulo_%28footballer%2C_born_June_1990%29)) |
| `marcou-por-bahia-e-fluminense` | Gilberto | arquibancada | Fluminense 2018, Bahia 2023, Bahia 2024 | **correct** | player's article names Fluminense, Bahia, Bahia ([source](https://pt.wikipedia.org/wiki/Gilberto_Moraes_Junior)) |
| `marcou-por-bahia-e-fluminense` | Biel | resenha | Fluminense 2021, Bahia 2023, Bahia 2024 | **correct** | player's article names Fluminense, Bahia, Bahia ([source](https://pt.wikipedia.org/wiki/Biel_Teixeira)) |
| `marcou-por-bahia-e-fluminense` | Daniel Sampaio Simões | enciclopedia | Fluminense 2019, Bahia 2020, Bahia 2021 | **correct** | player's article names Fluminense, Bahia, Bahia ([source](https://en.wikipedia.org/wiki/Danielzinho_%28footballer%2C_born_1996%29)) |
| `marcou-contra-internacional-2016` | Fred | arquibancada | Atlético-MG 2016 | **correct** | player's article names Atlético-MG ([source](https://pt.wikipedia.org/wiki/Frederico_Chaves_Guedes)) |
| `marcou-contra-internacional-2016` | Cleiton Xavier | raiz | Palmeiras 2016 | **correct** | player's article names Palmeiras ([source](https://pt.wikipedia.org/wiki/Cleiton_Xavier)) |
| `marcou-contra-internacional-2016` | Renato Baruffi | enciclopedia | Figueirense 2016 | **correct** | player's article names Figueirense ([source](https://en.wikipedia.org/wiki/Bady_%28footballer%29)) |
| `marcou-por-juventude-2021` | Wescley Gomes dos Santos | arquibancada | Juventude 2021 | **correct** | 1 Série A goal for Juventude in 2021, at Cuiabá on 29 May ([Wikipedia](https://en.wikipedia.org/wiki/Wescley_(footballer,_born_1991))) |
| `marcou-por-juventude-2021` | Guilherme Castilho | raiz | Juventude 2021 | **correct** | opened the scoring at Chapecoense, 14 Nov 2021 ([ESPN](https://africa.espn.com/football/match/_/gameId/598291)) |
| `marcou-por-juventude-2021` | Dawhan Fran Urano da Purificação Oliveira | enciclopedia | Juventude 2021 | **correct** | player's article names Juventude ([source](https://en.wikipedia.org/wiki/Dawhan)) |
| `marcou-contra-palmeiras-2025` | Hulk | arquibancada | Atlético-MG 2025 | **correct** | player's article names Atlético-MG ([source](https://pt.wikipedia.org/wiki/Hulk_%28futebolista%29)) |
| `marcou-contra-palmeiras-2025` | Pedro Raul | raiz | Ceará 2025 | **correct** | player's article names Ceará ([source](https://pt.wikipedia.org/wiki/Pedro_Raul)) |
| `marcou-contra-palmeiras-2025` | Lourenço | enciclopedia | Ceará 2025 | **correct** | player's article names Ceará ([source](https://en.wikipedia.org/wiki/Louren%C3%A7o_%28footballer%29)) |
| `marcou-por-sport-2025` | Sérgio Oliveira | arquibancada | Sport 2025 | **correct** | player's article names Sport ([source](https://pt.wikipedia.org/wiki/S%C3%A9rgio_Oliveira)) |
| `marcou-por-sport-2025` | Ramon Menezes | raiz | Sport 2025 | **correct** | player's article names Sport ([source](https://pt.wikipedia.org/wiki/Ramon_Menezes_Roma)) |
| `marcou-por-sport-2025` | Igor Cariús | enciclopedia | Sport 2025 | **correct** | player's article names Sport ([source](https://en.wikipedia.org/wiki/Igor_Cari%C3%BAs)) |
| `marcou-contra-flamengo-2024` | Philippe Coutinho | arquibancada | Vasco 2024 | **correct** | player's article names Vasco ([source](https://pt.wikipedia.org/wiki/Philippe_Coutinho)) |
| `marcou-contra-flamengo-2024` | Mateo Ponte | raiz | Botafogo 2024 | **correct** | player's article names Botafogo ([source](https://pt.wikipedia.org/wiki/Mateo_Ponte)) |
| `marcou-contra-flamengo-2024` | Mandaca | enciclopedia | Juventude 2024 | **correct** | player's article names Juventude ([source](https://en.wikipedia.org/wiki/Luis_Mandaca)) |

## Re-run on the final build (2026-11-05)
After the identity fixes from the generator reviews, `tools/fact_check.py` was re-run on an 85-day build with the same seed: 55 of 60 answers auto-confirmed (up from 50). The 5 others were not hand-checked in this run.
