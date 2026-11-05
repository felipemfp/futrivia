"""Club keys shared by every source (adaoduque spellings), with the names players see."""

DISPLAY = {
    "America-MG": "América-MG", "Athletico-PR": "Athletico-PR", "Atletico-GO": "Atlético-GO",
    "Atletico-MG": "Atlético-MG", "Avai": "Avaí", "Bahia": "Bahia", "Botafogo-RJ": "Botafogo",
    "Bragantino": "Bragantino", "CSA": "CSA", "Ceara": "Ceará", "Chapecoense": "Chapecoense",
    "Corinthians": "Corinthians", "Coritiba": "Coritiba", "Criciuma": "Criciúma", "Cruzeiro": "Cruzeiro",
    "Cuiaba": "Cuiabá", "Figueirense": "Figueirense", "Flamengo": "Flamengo", "Fluminense": "Fluminense",
    "Fortaleza": "Fortaleza", "Goias": "Goiás", "Gremio": "Grêmio", "Internacional": "Internacional",
    "Joinville": "Joinville", "Juventude": "Juventude", "Mirassol": "Mirassol", "Palmeiras": "Palmeiras",
    "Parana": "Paraná", "Ponte Preta": "Ponte Preta", "Remo": "Remo", "Santa Cruz": "Santa Cruz",
    "Santos": "Santos", "Sao Paulo": "São Paulo", "Sport": "Sport", "Vasco": "Vasco", "Vitoria": "Vitória",
}

# Transfermarkt club id -> club key, for every club in Série A 2025–2026.
TRANSFERMARKT = {
    "10010": "Bahia", "1023": "Palmeiras", "10492": "Juventude", "10870": "Fortaleza", "10997": "Remo",
    "17776": "Chapecoense", "199": "Corinthians", "2029": "Ceara", "210": "Gremio", "2125": "Vitoria",
    "221": "Santos", "2462": "Fluminense", "330": "Atletico-MG", "3876": "Mirassol", "537": "Botafogo-RJ",
    "585": "Sao Paulo", "609": "Cruzeiro", "614": "Flamengo", "6600": "Internacional", "679": "Athletico-PR",
    "776": "Coritiba", "8718": "Sport", "8793": "Bragantino", "978": "Vasco",
}


# Normalized words a Wikidata club label must contain to be this club. Generic words alone would match
# other clubs (Grêmio Mangaratibense, Internacional de Santa Maria), so ambiguous names carry a second word.
WIKIDATA_WORDS = {
    "America-MG": {"america"}, "Athletico-PR": {"paranaense"}, "Atletico-GO": {"goianiense"},
    "Atletico-MG": {"atletico", "mineiro"}, "Avai": {"avai"}, "Bahia": {"bahia"}, "Botafogo-RJ": {"botafogo", "regatas"},
    "Bragantino": {"bragantino"}, "CSA": {"alagoano"}, "Ceara": {"ceara", "sporting"}, "Chapecoense": {"chapecoense"},
    "Corinthians": {"corinthians", "paulista"}, "Coritiba": {"coritiba"}, "Criciuma": {"criciuma"},
    "Cruzeiro": {"cruzeiro", "esporte"}, "Cuiaba": {"cuiaba"}, "Figueirense": {"figueirense"},
    "Flamengo": {"regatas", "flamengo"}, "Fluminense": {"fluminense", "football"}, "Fortaleza": {"fortaleza", "esporte"},
    "Goias": {"goias", "esporte"}, "Gremio": {"gremio", "porto", "alegrense"}, "Internacional": {"sport", "internacional"},
    "Joinville": {"joinville"}, "Juventude": {"juventude", "esporte"}, "Mirassol": {"mirassol"},
    "Palmeiras": {"esportiva", "palmeiras"}, "Parana": {"parana", "clube"}, "Ponte Preta": {"ponte", "preta"},
    "Remo": {"remo"}, "Santa Cruz": {"santa", "cruz"}, "Santos": {"santos", "futebol"}, "Sao Paulo": {"sao", "paulo", "futebol"},
    "Sport": {"recife"}, "Vasco": {"vasco"}, "Vitoria": {"vitoria", "esporte"},
}


def display(club: str) -> str:
    return DISPLAY[club]
