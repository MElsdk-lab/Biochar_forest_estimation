# ============================================================
# data_config.py — Static Reference Data
# University of Pittsburgh | Biochar Feedstock Methodology
# All static dictionaries and lists used across notebooks
# ============================================================

import pandas as pd



# Forest Class Definitions
forestClasses = [
    {'code': 51, 'color': '4c7300', 'name': '51 Open evergreen broadleaved'},
    {'code': 52, 'color': '006400', 'name': '52 Closed evergreen broadleaved'},
    {'code': 61, 'color': 'a8c800', 'name': '61 Open deciduous broadleaved'},
    {'code': 62, 'color': '00a000', 'name': '62 Closed deciduous broadleaved'},
    {'code': 71, 'color': '005000', 'name': '71 Open evergreen needleleaved'},
    {'code': 72, 'color': '003c00', 'name': '72 Closed evergreen needleleaved'},
    {'code': 81, 'color': '286400', 'name': '81 Open deciduous needleleaved'},
    {'code': 82, 'color': '285000', 'name': '82 Closed deciduous needleleaved'},
    {'code': 91, 'color': 'a0b432', 'name': '91 Open mixed forest'},
    {'code': 92, 'color': '788200', 'name': '92 Closed mixed forest'},
]


# ── 1. FAO Regional Classification (LSIB-aligned) ────────────────────────────
FAO_LSIB_REGION = {
    "Africa": {
        "Central Africa": [
            "Cameroon", "Central African Rep", "Dem Rep of the Congo",
            "Rep of the Congo", "Equatorial Guinea", "Gabon", "Sao Tome & Principe"
        ],
        "East Africa": [
            "Burundi", "Djibouti", "Eritrea", "Ethiopia", "Kenya", "Rwanda",
            "Somalia", "Sudan", "Uganda"
        ],
        "Indian Ocean Islands": [
            "Comoros", "Madagascar", "Mauritius", "Seychelles"
        ],
        "Southern Africa": [
            "Angola", "Botswana", "Lesotho", "Malawi", "Mozambique", "Namibia",
            "South Africa", "Swaziland", "Tanzania", "Zambia", "Zimbabwe"
        ],
        "West Africa": [
            "Benin", "Burkina Faso", "Cabo Verde", "Chad", "Cote d'Ivoire",
            "Gambia, The", "Ghana", "Guinea", "Guinea-Bissau", "Liberia",
            "Mali", "Mauritania", "Niger", "Nigeria", "Senegal", "Sierra Leone", "Togo"
        ],
    },
    "Americas": {
        "Caribbean": [
            "Antigua & Barbuda", "Bahamas, The", "Barbados", "Belize", "Cuba",
            "Dominica", "Dominican Republic", "Grenada", "Guyana", "Haiti",
            "Jamaica", "St Kitts & Nevis", "Saint Lucia",
            "St Vincent & the Grenadines", "Suriname", "Trinidad & Tobago"
        ],
        "Central America and Mexico": [
            "Costa Rica", "El Salvador", "Guatemala", "Honduras",
            "Mexico", "Nicaragua", "Panama"
        ],
        "North America": ["Canada", "United States"],
        "South America": [
            "Argentina", "Bolivia", "Brazil", "Chile", "Colombia",
            "Ecuador", "Paraguay", "Peru", "Uruguay", "Venezuela"
        ],
    },
    "Europe": {
        "Eastern Europe": [
            "Albania", "Armenia", "Belarus", "Bosnia & Herzegovina", "Bulgaria",
            "Croatia", "Czechia", "Estonia", "Georgia", "Hungary", "Latvia",
            "Lithuania", "Montenegro", "Poland", "Moldova", "Romania",
            "Russia", "Serbia", "Slovakia", "Slovenia", "Macedonia", "Ukraine"
        ],
        "Western Europe": [
            "Andorra", "Austria", "Belgium", "Denmark", "Finland", "France",
            "Germany", "Greece", "Iceland", "Ireland", "Italy", "Liechtenstein",
            "Luxembourg", "Monaco", "Netherlands", "Norway", "Portugal",
            "San Marino", "Spain", "Sweden", "Switzerland", "United Kingdom"
        ],
    },
    "Near East": {
        "Central Asia": [
            "Azerbaijan", "Kazakhstan", "Kyrgyzstan", "Tajikistan",
            "Turkmenistan", "Uzbekistan"
        ],
        "South/East Mediterranean": [
            "Algeria", "Cyprus", "Egypt", "Israel", "Jordan", "Lebanon",
            "Libya", "Malta", "Morocco", "Syria", "Tunisia", "West Bank"
        ],
        "West Asia": [
            "Afghanistan", "Bahrain", "Iran", "Iraq", "Kuwait", "Oman",
            "Pakistan", "Qatar", "Saudi Arabia", "Turkey",
            "United Arab Emirates", "Yemen"
        ],
    },
    "Asia and the Pacific": {
        "East Asia": ["China", "Korea, North", "Japan", "Mongolia", "Korea, South"],
        "Pacific Region": [
            "Australia", "Cook Is", "Fiji", "Kiribati", "Marshall Is",
            "Fed States of Micronesia", "Nauru", "New Zealand", "Niue",
            "Palau", "Papua New Guinea", "Samoa", "Solomon Is",
            "Tonga", "Tuvalu", "Vanuatu"
        ],
        "South Asia": ["Bangladesh", "Bhutan", "India", "Maldives", "Nepal", "Sri Lanka"],
        "Southeast Asia": [
            "Brunei", "Cambodia", "Indonesia", "Laos", "Malaysia", "Burma",
            "Philippines", "Singapore", "Thailand", "Timor-Leste", "Vietnam"
        ],
    },
}


# ──  region country lists ─────────────────────

americas_countries = [c for sub in FAO_LSIB_REGION["Americas"].values() for c in sub]

europe_countries = [c for sub in FAO_LSIB_REGION["Europe"].values() for c in sub]

africa_forest_countries = [
    c for key, sub in FAO_LSIB_REGION["Africa"].items() 
    for c in sub
]

asia_pacific_countries = [
    c for key, sub in FAO_LSIB_REGION["Asia and the Pacific"].items()
    for c in sub
]

near_east_countries = [
    c for key, sub in FAO_LSIB_REGION["Near East"].items()
    for c in sub
]

# ──  region country lists with keeping the same strucutre  ─────────────────────

americas_region = {"Americas": FAO_LSIB_REGION["Americas"]}
europe_region   = {"Europe": FAO_LSIB_REGION["Europe"]}
africa_region   = {"Africa": FAO_LSIB_REGION["Africa"]}
asia_region     = {"Asia and the Pacific": FAO_LSIB_REGION["Asia and the Pacific"]}
near_east_region = {"Near East": FAO_LSIB_REGION["Near East"]}


# ── 2. US State Names ─────────────────────────────────────────────────────────
us_state_names = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
    "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
    "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
    "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
    "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
    "New Hampshire", "New Jersey", "New Mexico", "New York",
    "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
    "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
    "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
    "West Virginia", "Wisconsin", "Wyoming"
]


# ── 3. FAO Name Fix — FAO official names → LSIB-aligned names ────────────────
FAO_name_fix = {
    'Democratic Republic of the Congo':                     'Dem Rep of the Congo',
    'Congo':                                                'Rep of the Congo',
    'Iran (Islamic Republic of)':                           'Iran',
    'Syrian Arab Republic':                                 'Syria',
    "Lao People's Democratic Republic":                     'Laos',
    "Democratic People's Republic of Korea":                'Korea, North',
    'Republic of Korea':                                    'Korea, South',
    'Viet Nam':                                             'Vietnam',
    'Myanmar':                                              'Burma',
    'Türkiye':                                              'Turkey',
    'Brunei Darussalam':                                    'Brunei',
    'United Republic of Tanzania':                          'Tanzania',
    'United States of America':                             'United States',
    'Eswatini':                                             'Swaziland',
    "Côte d'Ivoire":                                        "Cote d'Ivoire",
    'Gambia':                                               'Gambia, The',
    'Bahamas':                                              'Bahamas, The',
    'Sao Tome and Principe':                                'Sao Tome & Principe',
    'Antigua and Barbuda':                                  'Antigua & Barbuda',
    'Saint Kitts and Nevis':                                'St Kitts & Nevis',
    'Saint Vincent and the Grenadines':                     'St Vincent & the Grenadines',
    'Trinidad and Tobago':                                  'Trinidad & Tobago',
    'Central African Republic':                             'Central African Rep',
    'Palestine':                                            'West Bank',
    'Bosnia and Herzegovina':                               'Bosnia & Herzegovina',
    'Russian Federation':                                   'Russia',
    'Bolivia (Plurinational State of)':                     'Bolivia',
    'Venezuela (Bolivarian Republic of)':                   'Venezuela',
    'North Macedonia':                                      'Macedonia',
    'Republic of Moldova':                                  'Moldova',
    'Micronesia (Federated States of)':                     'Fed States of Micronesia',
    'Cook Islands':                                         'Cook Is',
    'Marshall Islands':                                     'Marshall Is',
    'Solomon Islands':                                      'Solomon Is',
    'United Kingdom of Great Britain and Northern Ireland': 'United Kingdom',
}


# ── 4. FAO FRA 2025 Forest Area by Country (1 000 ha) ────────────────────────
fao_fra_2025_raw_data = [
    # country, 1990, 2000, 2010, 2015, 2020, 2025
    ["Afghanistan", 1209, 1209, 1209, 1209, 1209, 1209],
    ["Albania", 789, 769, 782, 797, 941, 941],
    ["Algeria", 1715, 1708, 1701, 1698, 1695, 1691],
    ["Andorra", 18, 17, 18, 18, 18, 18],
    ["Angola", 77533, 76013, 70913, 68363, 65812, 63262],
    ["Antigua and Barbuda", 10, 9, 9, 8, 8, 8],
    ["Argentina", 55990, 53442, 49727, 48444, 47496, 46598],
    ["Armenia", 335, 333, 332, 334, 334, 334],
    ["Australia", 134575, 132907, 131171, 132508, 133291, 133562],
    ["Austria", 3776, 3838, 3862, 3876, 3890, 3904],
    ["Azerbaijan", 945, 987, 1032, 1078, 1161, 1214],
    ["Bahamas", 510, 510, 510, 510, 510, 510],
    ["Bahrain", 1, 1, 1, 1, 2, 4],
    ["Bangladesh", 1985, 1920, 1888, 1883, 1878, 1873],
    ["Barbados", 6, 6, 6, 6, 6, 6],
    ["Belarus", 7780, 8273, 8630, 8634, 8843, 8975],
    ["Belgium", 677, 667, 690, 689, 671, 671],
    ["Belize", 1580, 1504, 1428, 1390, 1353, 1315],
    ["Benin", 6980, 5674, 4264, 3507, 3320, 3133],
    ["Bhutan", 2507, 2606, 2705, 2715, 2717, 2675],
    ["Bolivia (Plurinational State of)", 61774, 59086, 57500, 56687, 55569, 54370],
    ["Bosnia and Herzegovina", 2210, 2112, 2103, 2161, 2157, 2162],
    ["Botswana", 15728, 15728, 15728, 15728, 15730, 15730],
    ["Brazil", 618443, 560720, 525087, 515509, 502367, 486087],
    ["Brunei Darussalam", 413, 397, 380, 380, 380, 380],
    ["Bulgaria", 3327, 3375, 3737, 3833, 3896, 3959],
    ["Burkina Faso", 8299, 6378, 5035, 4436, 3836, 3237],
    ["Burundi", 276, 194, 194, 280, 280, 280],
    ["Cabo Verde", 34, 38, 42, 45, 48, 51],
    ["Cambodia", 11005, 10781, 10589, 8847, 7877, 6333],
    ["Cameroon", 22500, 21597, 20900, 20620, 19728, 19143],
    ["Canada", 360777, 360305, 365431, 367994, 368868, 368819],
    ["Central African Republic", 46435, 46085, 45735, 45560, 45327, 45095],
    ["Chad", 6730, 6353, 5530, 4890, 4251, 3611],
    ["Chile", 16811, 17425, 18038, 18217, 18186, 18162],
    ["China", 157141, 177001, 200610, 210294, 219098, 227153],
    ["Colombia", 65103, 62570, 61432, 60964, 60123, 59457],
    ["Comoros", 47, 43, 37, 35, 33, 33],
    ["Congo", 22255, 22135, 22015, 21913, 21784, 21854],
    ["Cook Islands", 15, 16, 16, 16, 16, 16],
    ["Costa Rica", 2759, 2849, 2881, 2954, 2972, 2990],
    ["Côte d'Ivoire", 8297, 6163, 4998, 4449, 4178, 3774],
    ["Croatia", 1850, 1885, 1920, 1922, 1940, 1946],
    ["Cuba", 2312, 2699, 3209, 3519, 3611, 3622],
    ["Cyprus", 161, 172, 173, 173, 173, 172],
    ["Czechia", 2839, 2865, 2880, 2893, 2923, 2968],
    ["Democratic People's Republic of Korea", 7455, 7455, 7558, 7614, 7671, 7728],
    ["Democratic Republic of the Congo", 160540, 153790, 147040, 142018, 140604, 139189],
    ["Denmark", 531, 572, 586, 624, 633, 643],
    ["Djibouti", 6, 6, 6, 6, 6, 6],
    ["Dominica", 59, 59, 58, 58, 58, 57],
    ["Dominican Republic", 2132, 2166, 2186, 2215, 2224, 2257],
    ["Ecuador", 14632, 13731, 13028, 12819, 12461, 12310],
    ["Egypt", 4, 4, 4, 4, 4, 4],
    ["El Salvador", 736, 706, 676, 676, 681, 685],
    ["Equatorial Guinea", 2699, 2616, 2533, 2490, 2448, 2407],
    ["Eritrea", 1651, 1592, 1532, 1502, 1472, 1442],
    ["Estonia", 2206, 2239, 2336, 2421, 2444, 2447],
    ["Eswatini", 486, 471, 456, 448, 441, 433],
    ["Ethiopia", 28538, 27809, 27081, 26786, 26767, 26747],
    ["Fiji", 940, 1006, 1067, 1090, 1113, 1137],
    ["Finland", 21875, 22446, 22242, 22409, 22543, 22543],
    ["France", 14436, 15288, 16419, 16836, 17348, 17795],
    ["Gabon", 23774, 23702, 23683, 23623, 23589, 23555],
    ["Gambia", 415, 358, 300, 271, 242, 209],
    ["Georgia", 3030, 3039, 3101, 3101, 3101, 3101],
    ["Germany", 11300, 11354, 11409, 11433, 11457, 11481],
    ["Ghana", 5806, 6163, 6521, 6699, 6878, 7056],
    ["Greece", 3709, 3709, 3721, 4098, 4763, 4763],
    ["Grenada", 18, 18, 18, 18, 18, 18],
    ["Guatemala", 4852, 4227, 3756, 3671, 3602, 3536],
    ["Guinea", 7202, 6532, 5862, 5527, 5192, 4857],
    ["Guinea-Bissau", 2257, 2207, 2163, 2142, 2121, 2100],
    ["Guyana", 18602, 18564, 18520, 18461, 18415, 18377],
    ["Haiti", 369, 384, 380, 364, 365, 372],
    ["Honduras", 7644, 7129, 6745, 6527, 6112, 5861],
    ["Hungary", 1814, 1921, 2046, 2061, 2057, 2087],
    ["Iceland", 18, 32, 49, 53, 57, 61],
    ["India", 63938, 67591, 69496, 70828, 72309, 72739],
    ["Indonesia", 116335, 91959, 96305, 95028, 95562, 95969],
    ["Iran (Islamic Republic of)", 10751, 10751, 10751, 10751, 10751, 10751],
    ["Iraq", 804, 818, 804, 759, 726, 693],
    ["Ireland", 462, 630, 720, 755, 793, 833],
    ["Israel", 132, 153, 154, 165, 140, 150],
    ["Italy", 7590, 8369, 9028, 8907, 9360, 9422],
    ["Jamaica", 521, 521, 558, 577, 597, 616],
    ["Japan", 24950, 24876, 24966, 24944, 24919, 24908],
    ["Jordan", 71, 71, 71, 71, 71, 71],
    ["Kazakhstan", 3162, 3157, 3082, 3308, 3451, 3521],
    ["Kenya", 3741, 3816, 3878, 3384, 3591, 3914],
    ["Kiribati", 1, 1, 1, 1, 1, 1],
    ["Kuwait", 3, 5, 5, 6, 6, 6],
    ["Kyrgyzstan", 1136, 1181, 1227, 1247, 1255, 1255],
    ["Lao People's Democratic Republic", 14399, 14050, 13661, 13369, 13213, 13036],
    ["Latvia", 3173, 3241, 3372, 3399, 3434, 3467],
    ["Lebanon", 138, 139, 140, 140, 141, 141],
    ["Lesotho", 35, 35, 35, 35, 35, 35],
    ["Liberia", 8009, 8009, 7620, 7037, 6529, 6327],
    ["Libya", 217, 214, 210, 209, 207, 205],
    ["Liechtenstein", 5, 5, 6, 6, 6, 6],
    ["Lithuania", 1945, 2020, 2170, 2187, 2202, 2216],
    ["Luxembourg", 86, 87, 89, 89, 89, 89],
    ["Madagascar", 13677, 13014, 11946, 11146, 10543, 9922],
    ["Malawi", 3502, 3082, 2662, 2452, 2242, 2032],
    ["Malaysia", 20619, 19691, 18948, 19464, 19185, 18885],
    ["Maldives", 4, 4, 4, 4, 4, 4],
    ["Mali", 13998, 12993, 11987, 11485, 10982, 10479],
    ["Malta", 0, 0, 0, 0, 0, 0],
    ["Marshall Islands", 9, 9, 9, 9, 10, 10],
    ["Mauritania", 927, 953, 980, 993, 1006, 1019],
    ["Mauritius", 41, 42, 38, 38, 38, 38],
    ["Mexico", 71804, 69594, 68156, 67543, 66904, 66266],
    ["Micronesia (Federated States of)", 64, 64, 64, 64, 64, 65],
    ["Monaco", 0, 0, 0, 0, 0, 0],
    ["Mongolia", 14352, 14264, 14184, 14178, 14178, 14178],
    ["Montenegro", 626, 626, 827, 827, 827, 827],
    ["Morocco", 5701, 5699, 5696, 5690, 5694, 5695],
    ["Mozambique", 41589, 38919, 36248, 34913, 33578, 32243],
    ["Myanmar", 39218, 34868, 31441, 29992, 28544, 27095],
    ["Namibia", 8769, 8059, 8053, 8049, 8046, 8043],
    ["Nauru", 0, 0, 0, 0, 0, 0],
    ["Nepal", 5748, 5916, 6083, 6100, 6183, 6266],
    ["Netherlands", 345, 360, 373, 365, 367, 369],
    ["New Zealand", 9372, 9850, 9848, 9847, 9965, 10303],
    ["Nicaragua", 7099, 6106, 5113, 5002, 4891, 4781],
    ["Niger", 1945, 1328, 1204, 1142, 1080, 1055],
    ["Nigeria", 21571, 20302, 19033, 18399, 17764, 17130],
    ["Niue", 19, 19, 19, 19, 19, 19],
    ["North Macedonia", 912, 958, 960, 994, 1042, 1026],
    ["Norway", 12217, 12198, 12149, 12133, 12121, 12109],
    ["Oman", 2, 2, 2, 2, 2, 2],
    ["Pakistan", 3461, 3317, 3165, 3036, 3089, 3192],
    ["Palau", 38, 40, 41, 41, 41, 42],
    ["Palestine", 9, 9, 10, 11, 11, 11],
    ["Panama", 4956, 4791, 4677, 4645, 4630, 4615],
    ["Papua New Guinea", 34614, 34395, 34176, 34153, 34048, 34029],
    ["Paraguay", 25680, 21910, 18140, 16370, 15116, 14297],
    ["Peru", 77038, 74045, 71051, 69554, 68656, 67160],
    ["Philippines", 7779, 7309, 6840, 7014, 7226, 7439],
    ["Poland", 8882, 9059, 9329, 9420, 9464, 9495],
    ["Portugal", 3438, 3349, 3252, 3312, 3334, 3363],
    ["Qatar", 1, 1, 1, 1, 1, 1],
    ["Republic of Korea", 6551, 6476, 6387, 6337, 6298, 6279],
    ["Republic of Moldova", 325, 344, 375, 386, 373, 370],
    ["Romania", 6371, 6366, 6515, 6901, 6929, 6957],
    ["Russian Federation", 811641, 812445, 821502, 823206, 828432, 832630],
    ["Rwanda", 437, 409, 416, 489, 562, 635],
    ["Saint Kitts and Nevis", 11, 11, 11, 11, 11, 11],
    ["Saint Lucia", 27, 29, 31, 32, 33, 33],
    ["Saint Vincent and the Grenadines", 29, 29, 29, 29, 29, 29],
    ["Samoa", 177, 172, 167, 165, 162, 160],
    ["San Marino", 1, 1, 1, 1, 1, 1],
    ["Sao Tome and Principe", 59, 59, 58, 55, 55, 55],
    ["Saudi Arabia", 2768, 2768, 2768, 2768, 2768, 2776],
    ["Senegal", 9193, 9038, 8882, 8805, 8727, 8649],
    ["Serbia", 2313, 2483, 2880, 3078, 3277, 3475],
    ["Seychelles", 34, 32, 30, 29, 28, 27],
    ["Sierra Leone", 3127, 2929, 2732, 2634, 2535, 2436],
    ["Singapore", 15, 17, 18, 16, 16, 16],
    ["Slovakia", 1902, 1901, 1918, 1922, 1931, 1940],
    ["Slovenia", 1188, 1233, 1247, 1248, 1244, 1244],
    ["Solomon Islands", 2540, 2532, 2525, 2521, 2518, 2514],
    ["Somalia", 8284, 7516, 6749, 5979, 5210, 4830],
    ["South Africa", 19817, 20692, 21568, 22006, 22444, 22881],
    ["Spain", 13905, 17094, 18566, 18575, 18982, 19133],
    ["Sri Lanka", 2370, 2231, 2156, 2098, 2145, 2121],
    ["Sudan", 28075, 26334, 24593, 23722, 22851, 21980],
    ["Suriname", 14866, 14902, 14862, 14839, 14765, 14674],
    ["Sweden", 28063, 28163, 28073, 27980, 27934, 27934],
    ["Switzerland", 1154, 1196, 1235, 1249, 1258, 1267],
    ["Syrian Arab Republic", 451, 461, 512, 527, 528, 528],
    ["Tajikistan", 408, 410, 410, 422, 423, 425],
    ["Thailand", 20235, 20165, 20095, 20060, 20338, 19647],
    ["Timor-Leste", 1101, 1087, 1073, 1066, 1059, 1054],
    ["Togo", 1298, 1268, 1239, 1224, 1209, 1224],
    ["Tonga", 9, 9, 9, 9, 9, 9],
    ["Trinidad and Tobago", 241, 237, 232, 230, 228, 226],
    ["Tunisia", 644, 668, 703, 705, 699, 687],
    ["Türkiye", 19783, 20148, 21083, 21630, 22220, 22806],
    ["Turkmenistan", 2330, 2330, 2330, 2330, 2330, 2330],
    ["Tuvalu", 1, 1, 1, 1, 1, 1],
    ["Uganda", 4548, 3401, 2899, 2649, 2508, 2368],
    ["Ukraine", 9274, 9510, 9548, 9700, 9900, 10090],
    ["United Arab Emirates", 315, 315, 320, 321, 323, 325],
    ["United Kingdom", 2778, 2954, 3059, 3155, 3215, 3278],
    ["United Republic of Tanzania", 58165, 54135, 50105, 48090, 45745, 43400],
    ["United States of America", 302450, 303536, 308720, 310095, 309255, 308895],
    ["Uruguay", 879, 1336, 1696, 1834, 1932, 2024],
    ["Uzbekistan", 2549, 2961, 3350, 3549, 3689, 3894],
    ["Vanuatu", 991, 967, 943, 931, 919, 907],
    ["Venezuela (Bolivarian Republic of)", 50484, 49232, 48382, 47879, 47335, 47088],
    ["Viet Nam", 9376, 11784, 13388, 14062, 14677, 14790],
    ["Yemen", 549, 549, 549, 549, 549, 549],
    ["Zambia", 47412, 47054, 46696, 45755, 45360, 44874],
    ["Zimbabwe", 16715, 15658, 14601, 14303, 14031, 13766],
]

fao_fra_2025_raw_data = pd.DataFrame(
    fao_fra_2025_raw_data,
    columns=['country', '1990_area_Mha', '2000_area_Mha', '2010_area_Mha', '2015_area_Mha', '2020_area_Mha', '2025_area_Mha']
)


# ── 5. Helper Functions ───────────────────────────────────────────────────────
def get_all_countries(regions):
    """Return a flat sorted list of all country names."""
    countries = []
    for region in regions.values():
        for subregion_countries in region.values():
            countries.extend(subregion_countries)
    return sorted(countries)


def build_country_lookup(regions):
    """Return a dict mapping country name → {region, subregion}."""
    lookup = {}
    for region_name, subregions in regions.items():
        for subregion_name, countries in subregions.items():
            for country in countries:
                lookup[country] = {
                    "region": region_name,
                    "subregion": subregion_name
                }
    return lookup

# ── 6. Tree cover threshold────────────────────────────────────────────────────────────
country_thresholds = [10, 20, 30, 40, 50]
state_thresholds   = [10, 20, 30, 40, 50]

# ── Tree cover bins────────────────────────────────────────────────────────────

forest_bins = list(range(10, 110, 10))


# ── 7. FAO FRA 2025 Regional Detailed Tables ─────────────────────────────────
# Source: FAO FRA 2025 regional summary tables 
#Link: https://openknowledge.fao.org/server/api/core/bitstreams/2dee6e93-1988-4659-aa89-30dd20b43b15/content/FRA-2025/annexes.html
# Units: Million ha (unless otherwise noted)

fao_fra_2025_world = pd.DataFrame([
    ["Forest area",                   4344, 4237, 4201, 4181, 4165, 4140],
    ["Naturally regenerating forest", 4133, 3994, 3915, 3878, 3843, 3808],
    ["Planted forest",                 184,  215,  258,  275,  294,  304],
    ["Plantation forest",               86,  102,  130,  140,  152,  157],
    ["Primary forest",                1238, 1203, 1160, 1144, 1135, 1128],
    ["Mangroves",                     15.3, 15.0, 14.9, 14.9, 15.1, 15.5],
    ["Forest in protected areas",      507,  567,  684,  717,  733,  758],
    ["Forest with management plans",  1711, 1801, 1930, 1992, 2046, 2076],
], columns=['variable', '1990', '2000', '2010', '2015', '2020', '2025'])

fao_fra_2025_africa = pd.DataFrame([
    ["Forest area",                    780,  747,  713,  692,  677,  663],
    ["Naturally regenerating forest",  771,  737,  702,  680,  664,  649],
    ["Planted forest",                 8.9,  9.9, 11.3, 12.2, 13.3, 14.1],
    ["Plantation forest",              8.2,  8.9,  9.8, 10.3, 11.2, 11.8],
    ["Primary forest",                 191,  184,  175,  169,  166,  163],
    ["Mangroves",                     3.31, 3.24, 3.24, 3.31, 3.25, 3.28],
    ["Forest in protected areas",      119,  122,  135,  144,  146,  154],
    ["Forest with management plans",    75,   73,   92,  112,  125,  143],
], columns=['variable', '1990', '2000', '2010', '2015', '2020', '2025'])

fao_fra_2025_asia = pd.DataFrame([
    ["Forest area",                    582,  578,  605,  614,  624,  630],
    ["Naturally regenerating forest",  497,  480,  486,  486,  483,  484],
    ["Planted forest",                  85,   98,  120,  128,  141,  146],
    ["Plantation forest",               58,   68,   85,   90,  100,  104],
    ["Primary forest",                  95,   85,   81,   80,   82,   82],
    ["Mangroves",                     6.03, 6.10, 5.85, 5.66, 5.69, 6.10],
    ["Forest in protected areas",      100,  119,  145,  148,  152,  154],
    ["Forest with management plans",   228,  289,  318,  339,  364,  365],
], columns=['variable', '1990', '2000', '2010', '2015', '2020', '2025'])

fao_fra_2025_europe = pd.DataFrame([
    ["Forest area",                    998, 1006, 1021, 1025, 1033, 1039],
    ["Naturally regenerating forest",  913,  916,  925,  927,  934,  939],
    ["Planted forest",                  57,   62,   68,   70,   71,   71],
    ["Plantation forest",              3.6,  4.0,  4.4,  4.2,  4.1,  4.1],
    ["Primary forest",                 304,  305,  308,  309,  309,  310],
    ["Mangroves",                        0,    0,    0,    0,    0,    0],
    ["Forest in protected areas",      164,  178,  203,  214,  219,  227],
    ["Forest with management plans",   932,  935,  942,  947,  956,  962],
], columns=['variable', '1990', '2000', '2010', '2015', '2020', '2025'])

fao_fra_2025_north_central_america = pd.DataFrame([
    ["Forest area",                    771,  768,  776,  779,  778,  776],
    ["Naturally regenerating forest",  748,  735,  735,  735,  730,  726],
    ["Planted forest",                23.1, 32.7, 40.8, 44.0, 47.4, 49.8],
    ["Plantation forest",              6.4,  9.2, 13.3, 14.0, 15.2, 15.4],
    ["Primary forest",                 266,  261,  245,  238,  235,  235],
    ["Mangroves",                     2.32, 2.32, 2.35, 2.34, 2.35, 2.38],
    ["Forest in protected areas",     42.0, 51.5, 72.5, 73.8, 76.8, 81.1],
    ["Forest with management plans",   415,  426,  440,  449,  447,  447],
], columns=['variable', '1990', '2000', '2010', '2015', '2020', '2025'])

fao_fra_2025_oceania = pd.DataFrame([
    ["Forest area",                    184,  183,  181,  182,  183,  184],
    ["Naturally regenerating forest",  182,  179,  176,  178,  179,  179],
    ["Planted forest",                2.84, 3.84, 4.71, 4.69, 4.62, 4.92],
    ["Plantation forest",             2.81, 3.81, 4.37, 4.35, 4.28, 4.55],
    ["Primary forest",                39.1, 38.9, 38.8, 38.6, 38.5, 38.3],
    ["Mangroves",                     1.48, 1.21, 1.34, 1.28, 1.54, 1.54],
    ["Forest in protected areas",     19.2, 22.6, 27.6, 28.9, 29.1, 29.1],
    ["Forest with management plans",  11.4, 12.1, 12.5, 12.4, 12.5, 12.5],
], columns=['variable', '1990', '2000', '2010', '2015', '2020', '2025'])

fao_fra_2025_south_america = pd.DataFrame([
    ["Forest area",                   1028,  955,  906,  890,  870,  849],
    ["Naturally regenerating forest", 1022,  946,  892,  872,  853,  831],
    ["Planted forest",                 6.6,  8.6, 13.9, 17.2, 17.2, 17.3],
    ["Plantation forest",              6.6,  8.6, 13.9, 17.1, 17.2, 17.3],
    ["Primary forest",                 342,  329,  313,  309,  303,  299],
    ["Mangroves",                     2.21, 2.17, 2.09, 2.28, 2.26, 2.23],
    ["Forest in protected areas",       63,   73,  102,  108,  110,  112],
    ["Forest with management plans",    50,   65,  125,  134,  141,  147],
], columns=['variable', '1990', '2000', '2010', '2015', '2020', '2025'])

# ── Summary: forest area only by region ──────────────────────────────────────
fao_fra_2025_regional = pd.DataFrame([
    ["Africa",                   780, 747, 713, 692, 677, 663],
    ["Asia",                     582, 578, 605, 614, 624, 630],
    ["Europe",                   998, 1006, 1021, 1025, 1033, 1039],
    ["North and Central America", 771, 768, 776, 779, 778, 776],
    ["Oceania",                  184, 183, 181, 182, 183, 184],
    ["South America",           1028, 955, 906, 890, 870, 849],
    ["World",                   4344, 4237, 4201, 4181, 4165, 4140],
], columns=['region', '1990', '2000', '2010', '2015', '2020', '2025'])


# ──   ────────────────────────────────────────────────────────────


testing_sample = [
    # Americas
    'United States', 'Canada', 'Brazil',
    # Europe (with Russia)
    'France', 'Spain', 'Italy', 'Sweden', 'Finland', 'Norway', 'Poland', 'Russia',
    # Asia
    'China', 'India', 'Indonesia', 'Malaysia',
    # Africa
    'Dem Rep of the Congo', 'Cameroon', 'Tanzania', 'Nigeria', 'Ethiopia', 'South Africa'
]
# ── Confirm loaded ────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print(f'✅ FAO_LSIB_REGION: {len(FAO_LSIB_REGION)} regions')
    print(f'✅ us_state_names: {len(us_state_names)} states')
    print(f'✅ FAO_name_fix: {len(FAO_name_fix)} entries')
    print(f'✅ fao_fra_2025: {len(fao_fra_2025)} countries')
    print(f'✅ fao_fra_2025_regional: {len(fao_fra_2025_regional)} regions + world')
    print(f'✅ fao_fra_2025_world: {len(fao_fra_2025_world)} variables')
    print(f'✅ fao_fra_2025_africa: {len(fao_fra_2025_africa)} variables')
    print(f'✅ fao_fra_2025_asia: {len(fao_fra_2025_asia)} variables')
    print(f'✅ fao_fra_2025_europe: {len(fao_fra_2025_europe)} variables')
    print(f'✅ fao_fra_2025_north_central_america: {len(fao_fra_2025_north_central_america)} variables')
    print(f'✅ fao_fra_2025_oceania: {len(fao_fra_2025_oceania)} variables')
    print(f'✅ fao_fra_2025_south_america: {len(fao_fra_2025_south_america)} variables')
    print(f'✅ Total FAO_LSIB countries: {len(get_all_countries(FAO_LSIB_REGION))}')
