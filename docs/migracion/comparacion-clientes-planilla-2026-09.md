# Comparación clientes Excel vs ScobyERP (2026-09-11)

Fuente: `datos a migrar/0926 - Base de datos Clientes Kombucha.xlsx` (hojas *CLIENTE EMPRESA* y *CLIENTE PARTICULAR*) vs. los 283 clientes actuales en producción (`titourcia.com/scobyerp`, tras la limpieza de duplicados de ayer, #138).

Clasificación automática por similitud de texto del nombre — **no reemplaza la revisión de Scoby**, es un punto de partida para acelerarla. "Excel" es el nombre comercial (columna *Nombre* en Empresa, *Nombre Cliente* en Particular); en Empresa también se probó contra la *Razón Social*.


## CLIENTE EMPRESA (70 filas)

- **Alta confianza (score ≥ 0.90):** 41
- **Media confianza / ambiguo (0.60–0.89), requiere confirmación:** 20
- **Sin coincidencia — posible cliente nuevo:** 9

### Alta confianza

| Excel | RUT | Región | Comuna | Teléfono | Estado | ScobyERP |
|---|---|---|---|---|---|---|
| Emporio de la Tierra | - | RM | Santiago centro | 56990186096 | - | #79 Emporio de la Tierra |
| Espacio Regenera | 76.515.242-9 | RM | Providencia | 56964488135 | - | #48 Espacio Regenera |
| La Selecta | 13.763.838-K | V | Villa Alemana | 56966072083 | - | #77 La selecta |
| Frutos con Sentido | 77.578.269-2 | RM | Ñuñoa | 56993081454 | - | #52 Frutos con Sentido |
| Casa Kutral | 77.138.277-0 | V | Maitencillo | 56953571459 | - | #26 Casa Kutral |
| Cocca Casa Bar | - | RM | Ñuñoa | 56935930054 | - | #84 Cocca Casa Bar |
| Acentto Café | 15.327.031-7 | V | Viña del mar | 56930661372 | - | #63 Acentto Cafe |
| Moneda a granel | 77.901.686-2 | RM | Santiago centro | 56978025881 | - | #27 Moneda a Granel |
| Sar Coffee | 77.846.599-k | V | Villa Alemana | 56982145995 | - | #210 SAR Coffee |
| Tavola  | 76.157.953-3 | RM | Huechuraba | 56948112029 | - | #123 Tavola |
| Setu  | 78.118.937-5 | V | Concon | 56963981121 | - | #140 Setu |
| El Refill | 78.134.314-5 | V | Concon | 56995300300 | - | #96 ElRefill |
| Marai | 77.000.145-5 | V | Concon | 56964652704 | - | #219 Marai |
| Emporio Clarifa | 77.504.706-2 | V | Quilpué | 56965715697 | - | #90 Emporio Clarifa |
| Madrissima | 77.751.106-8 | RM | Providencia | 56992144199 | - | #99 Madrissima |
| Stefani | 78.036.212-K | V | Valparaiso | 975437001 | - | #91 Stefani |
| Deli Market | 77.219.952-K | V | Viña Del Mar  | 56979432717 | - | #131 Deli Market |
| Food Roots | 77.156.424-0 | V | Concon | 56976158574 | - | #191 food root |
| Le Rouge  | 78.118.653-8 | V | Concon | 56977531826 | - | #85 Le Rouge |
| Virgin Coffee | 77.296417-K | V | Reñaca | 56983002545 | - | #159 Virgin Cofee |
| Lore Cuisine | 77.081.323-9 | V | Reñaca | 56934692159 | - | #93 Lore cousine |
| Emporio La Mocha | 77269286 | RM | San Miguel | 56932219802 | - | #75 Emporio la Mocha |
| Le Flaneur | 78.026.158-7 | V | Viña Del Mar  | 56940705600 | - | #46 Le Flaneur |
| Ambrosio | - | V | Viña Del Mar  | 56998621236 | - | #13 Ambrosio |
| La Farine  | 76.677.823-2 | V | Concon | 56934056411 | - | #12 La Farine |
| Fauna | 76.028.956-6 | V | Valparaiso | 56985490411 | - | #76 Fauna |
| Laguna surf | 78.297.986-8 | V | Laguna zapallar | 56978885209 | - | #182 Laguna Surf |
| K Bistrot | 76.999.687-7 | V | Viña Del Mar  | 56979471530 | - | #30 K Bistro |
| Heladeria Monterosso | - | V | Limache | 56999935850 | - | #181 Heladeria Monterosso |
| Instinto Café | 78.180.294-8 | V | Reñaca | 56989722855 | - | #195 instinto Cafe |
| Enfermentados | 77.603.366-9 | V | Viña Del Mar  | 995006193 | - | #147 Enfermentados |
| Rustikos | 77.578.315-k | V | Reñaca | 56999099413 | - | #11 Rustikos |
| Nicolas Café | 76.580.713-1 | RM | Providencia | 56990803671 | - | #158 NicolasCafe |
| El Chingao | 12.774.220-0 | V | Quillota | 56959703624 | - | #231 El Chingao |
| Dr.Oschilewski | 76.157.226-1 | V | Reñaca | 56987382717 | - | #136 Dr. Oschilewski |
| Gerardo | 78.116.691-k | V | Concon | 56982894641 | - | #20 Gerardo |
| Clan Market | - | V | Concon | 56934056411 | - | #50 Clan Market |
| Café con Letras | 78.055.976-4 | V | Viña Del Mar  | 56968449570 | - | #276 Cafe con Letras |
| Roberto Providencia  | 78.329.256-4 | RM | Providencia | 56965950563 | - | #179 Roberto Providencia |
| Kiosco Club Español Recreo | - | V | Viña Del Mar  | 56971410220 | - | #281 Kiosco Club Español Recreo |
| Sano Alimentos | 76.867.197-4 | V | Viña Del Mar  | 56978415375 | - | #260 SanoAlimentos |

### Media confianza / ambiguo — requiere confirmación

| Excel | RUT | Región | Comuna | Teléfono | Estado | Candidatos ScobyERP (score) |
|---|---|---|---|---|---|---|
| Oh Some Coffe | 76.745.135-0 | RM | Providencia | - | ok | #210 SAR Coffee (0.61) |
| Casa Garla | 76.901.515-9 | RM | Providencia | - | Cerrado | #26 Casa Kutral (0.67) |
| Ñuñork Café | 78.033.557- 2 | RM | Ñuñoa | 56995300545 | - | #195 instinto Cafe (0.67); #63 Acentto Cafe (0.61) |
| Tolima Coffee | 77.954.488-5 | RM | Ñuñoa | 56973652209 | - | #35 Tolima (0.85); #210 SAR Coffee (0.70) |
| De los Buenos Trigos | 77.583.033-6 | V | Limache | 56942302725 | - | #8 Buenos Trigos (0.85) |
| Pan Ceres | 77.772.045-7 | V | Quilpué | 56953391033 | - | #14 Ceres (0.85); #98 Panaderia Ceres (0.75) |
| Madre Tierra Reñaca | 77.884.652-7 | V | Reñaca | 56950169760 | - | #33 Novac (0.85); #152 Claudia Reñaca (0.67); #268 Maria Ignacia (0.62) |
| Tigro Cocina Vegana | 77.819.653-0 | V | Laguna Zapallar | 56984760092 | - | #28 Tigro (0.85) |
| Emporio la semilla | 11.860.039-8  | V | Nogales | 56950116501 | - | #75 Emporio la Mocha (0.76); #90 Emporio Clarifa (0.73); #244 Emporio Lucia Talca (0.70) |
| La Casa de Wagner | 77.702.098-6 | V | Limache | 56955176772 | - | #36 Wagner (0.85); #211 Lorena mama de Alex (0.61) |
| Da Mafalda | 78.031.648-9 | V | Valparaiso | 961731418 | - | #133 Mafalda (0.85) |
| Bodegon de la Familia | 7.598.708-0 | V | Quillota | 56942897411 | - | #168 Camila (0.85) |
| Carmen Café | 76.939.039-1 | V | Laguna zapallar | 56961533350 | - | #180 Carmen Cafe Laguna (0.85); #63 Acentto Cafe (0.70); #22 Mariana (0.67) |
| Cooperativa Marga Marga | 65.223.983-8 | V | Viña Del Mar  | - | - | #116 Marga Marga (0.85) |
| Coffee Time | 78.012.793-7 | V | Concon | - | Cerrado | #65 Coffe time concon (0.71) |
| El Mercadito | 77.935.666-3 | V | Concon | 56993278496 | - | #49 El Mercadito Concon (0.85); #88 El Camino (0.67) |
| Petit Bistrot | 78.053.102-9 | V | Reñaca | 56968155415 | - | #30 K Bistro (0.67) |
| Alma Market | 77.874.358-2 | V | Concon | 56992303968 | - | #50 Clan Market (0.73); #131 Deli Market (0.73); #277 Carla Mardones (0.64) |
| Arena Café | 77.384.005-9 | V | Laguna zapallar | 56961930052 | - | #175 Arena Cafe Maitencillo (0.85); #178 Loreto Amiga Arena Cafe (0.85); #63 Acentto Cafe (0.73) |
| Kombi store | 77.276.679-3 | V | Viña Del Mar  | 56957995968 | - | #274 Kombi (0.85); #30 K Bistro (0.63) |

### Sin coincidencia — ¿cliente nuevo?

| Excel | RUT | Región | Comuna | Teléfono | Estado |
|---|---|---|---|---|---|
| Casa 4409 | 76.582.658-6 | RM | Ñuñoa | - | cerrado |
| Multisaludable | 77.073.325-1 | RM | Las Condes | 56966777381 | Cerrado |
| De Calle | 76.327.010-6 | RM | Ñuñoa | - | Factura pendiente |
| Moléculas Store | 76.154.736-4 | RM | Providencia | - | Cerrado |
| Namsté | 66.146.656-2 | V | Viña del mar | - | cerrado |
| Yahgan | 76.286.103-8 | V | Viña del mar | 56977088164 | - |
| Fabrica Boulder | 77.794.322-7 | V | Valparaiso | 56942148771 | - |
| Zorzal Café | 77.683.489-0 | V | Quillota | 56988833421 | - |
| La Creme | 78.107.948-0 | V | Concon | 56958587558 | Cerrado |

## CLIENTE PARTICULAR (80 filas)

- **Alta confianza (score ≥ 0.90):** 33
- **Media confianza / ambiguo (0.60–0.89), requiere confirmación:** 41
- **Sin coincidencia — posible cliente nuevo:** 6

### Alta confianza

| Excel | Comuna | Teléfono | ScobyERP |
|---|---|---|---|
| Javier Cayulef | Santiago | 56993239737 | #60 Javier Cayulef |
| Roberto | Providencia | 56965950563 | #275 Roberto |
| Liliana Lopez | Providencia | 56963005384 | #31 Liliana Lopez |
| Patricia Merino | Peñalolen | 56998292566 | #40 Patricia merino |
| Mariel Sáez | Providencia | 56977051843 | #129 Mariel Saez |
| Carolina Bernuy | Peñalolen | 56987470667 | #37 Carolina Bernuy |
| Nidia Sáez | Ñuñoa | 56999090870 | #62 Nidia Saez |
| Claudia Arancibia | Providencia | 56965766168 | #110 Claudia Arancibia |
| Ignacio Morales | Ñuñoa | 56988149717 | #67 Ignacio Morales |
| Vanessa Barros | Las Condes | 56990600706 | #95 Vanessa Barros |
| Celso Gonzalez | Quillota | 56965112685 | #86 Celso Gonzalez |
| Cecilia Roblero | Providencia | 56990202644 | #264 Cecilia roblero |
| Ximena Sepulveda | Peñalolen | 56998722434 | #112 Ximena Sepulveda |
| Vale Mellado | La Florida | 56989851989 | #185 Vale Mellado |
| Paola Ipaarraguirre | Peñalolen | 56949537922 | #254 Paola Ipaaraguirre |
| Roberto | La Florida | 56971082391 | #275 Roberto |
| Nathalia Posada | Las Condes | 56981825999 | #39 Nathalia Posadas |
| Carla Zapata | La Reina | 56999978939 | #103 Carla Zapata |
| Soledad Osorio | La Cisterna | 56954012029 | #68 Soledad Osorio |
| Camila Navarrete | Ñuñoa | 56964690806 | #109 Camila NAvarrete |
| Danitza Saavedra | La Reina | 56962759517 | #245 Danitza saavedra |
| Javiera Barra | Quilpue | 56976048347 | #54 Javiera Barra |
| Ignacia | La Calera | 56981447301 | #270 Ignacia |
| Thiare | La Cruz | 56989346079 | #227 Thiare |
| Maria Jesus Alliende | Ñuñoa | 56990530308 | #32 Maria Jesus Allende |
| Paulina Vega | Ñuñoa | 56977593061 | #16 Paulina Vega |
| Luis Allende | Vitacura | 56988291648 | #145 Luis Allende |
| Claudio Milla | Concon | 56987751494 | #1 Claudio Milla |
| Gabriela Perez | Quillota | 56997648645 | #230 Gabriela Perez |
| Macarena Blanco | Reñaca | 56998215251 | #124 Macarena Blanco |
| Carla Mardones | Reñaca | 56999146463 | #277 Carla Mardones |
| Sonia Rublic | Reñaca | 56964960190 | #283 Sonia Reblic |
| Alejandra Parra | Quilpue | 56989587689 | #235 Alejandra Parra |

### Media confianza / ambiguo — requiere confirmación

| Excel | Comuna | Teléfono | Candidatos ScobyERP (score) |
|---|---|---|---|
| Roberto S. | Ñuñoa | 56982928838 | #275 Roberto (0.88); #171 Roberto Boleta (0.70) |
| Maria Eugenia | La Cruz | 56984261559 | #170 Maria (0.85); #104 Maria eugenia La Cruz (0.85); #268 Maria Ignacia (0.77) |
| Barbara Torres | Las Condes | 56972104536 | #149 Barbara Apoderada (0.65) |
| Diego Guaita | peñalolen | 56938989964 | #51 Diego Varas (0.70); #92 Bodegon Quillota (0.64); #207 Diego Artigas (0.64) |
| Maria Elena Pulido | Las Condes | 56976487746 | #170 Maria (0.85); #104 Maria eugenia La Cruz (0.62) |
| Javiera Bastias | Providencia | - | #4 Javier (0.85); #54 Javiera Barra (0.79); #154 Javiera Quilpue (0.60) |
| Maria Mena Oyarce | La Florida | 56982037222 | #170 Maria (0.85); #104 Maria eugenia La Cruz (0.63); #193 Valeria Mena (0.62) |
| Arazely | Independencia | 56973813401 | #257 Charly (0.62) |
| Nicolas Pavez | Quilpué | 56990829080 | #158 NicolasCafe (0.75); #160 Nicolas Rodriguez (0.67); #107 Nicolas Rojos (0.62) |
| Clauida Venegas | La Calera | 56956085057 | #72 Isa Venegas (0.77); #204 Claudia Vecina (0.76); #152 Claudia Reñaca (0.69) |
| Karen | Quilpué (Los Pinos) | 56959838791 | #192 Karim (0.60) |
| Jaime Marin | Las Condes | 56976637131 | #61 Julien / Mario (0.70); #12 La Farine (0.60) |
| Monica Lagos | Vitacura | 56977942488 | #137 Monica rosales (0.69) |
| Sebastian Catalán | Valparaiso | 56966112412 | #34 Sebastian gonzalez (0.69); #126 Sebastian Freund (0.67) |
| Carolina Gonzalez | La Reina | 56977677941 | #86 Celso Gonzalez (0.71); #34 Sebastian gonzalez (0.69); #37 Carolina Bernuy (0.62) |
| Paulina Araya | Ñuñoa | - | #16 Paulina Vega (0.72); #138 Catalina Arriagada (0.65); #110 Claudia Arancibia (0.60) |
| Paulina Bravo | Valparaiso | 56937845482 | #16 Paulina Vega (0.72) |
| Diego | Santiago centro | 56931816357 | #207 Diego Artigas (0.85); #51 Diego Varas (0.85); #164 Lydie (0.60) |
| Nicolás Perez | Ñuñoa | 56996131647 | #160 Nicolas Rodriguez (0.73); #107 Nicolas Rojos (0.69); #230 Gabriela Perez (0.67) |
| Diego | Santiago Centro | 56931816357 | #207 Diego Artigas (0.85); #51 Diego Varas (0.85); #164 Lydie (0.60) |
| Patricio | Quilpue | 56958047959 | #40 Patricia merino (0.70); #165 Patricia Quillota (0.64); #247 Priscila (0.62) |
| Cony Hetzer apoderada | Reñaca | 56961402818 | #18 apoderada (0.85); #184 Consuelo apoderada (0.72); #242 Loreto Apoderada (0.70) |
| Beatriz Sanchez  | Renaca | 56978784532 | #236 Nicolett sanchez (0.65); #129 Mariel Saez (0.62) |
| Bernardita Palma Apoderada | Concon | 56951190825 | #55 Bernardita Palma (0.85); #18 apoderada (0.85); #149 Barbara Apoderada (0.70) |
|  Constanza Montecinos Legacy | Reñaca | 56994445431 | #214 Constanza Montecinos (0.85); #258 Constanza Legacy (0.74) |
| Lorena mama Alex Apoderada | Concon | 56961213036 | #18 apoderada (0.85); #239 Lorena apoderada (0.76); #211 Lorena mama de Alex (0.71) |
| Loreto Reyes  Apoderada | Reñaca | 56942500113 | #250 Loreto Reyes (0.85); #18 apoderada (0.85); #242 Loreto Apoderada (0.84) |
| Carlos Viviani Apoderado | Reñaca | 56954123855 | #208 Carlos Apoderado (0.80); #64 Carlos Vivianni (0.72); #225 Maria Ignacia Apoderada (0.64) |
| Jota Vecino Apoderado | Reñaca | 56992284640 | #57 Jota (0.85); #69 vecino (0.85); #242 Loreto Apoderada (0.65) |
| Carlos Arriagada Apoderado | Reñaca | 56974993208 | #208 Carlos Apoderado (0.76); #225 Maria Ignacia Apoderada (0.65); #149 Barbara Apoderada (0.65) |
| Marion Censi Apoderada | Concon | 56973653830 | #23 Marion Censi (0.85); #18 apoderada (0.85); #225 Maria Ignacia Apoderada (0.76) |
| Guillaume Vichery Apoderado | Reñaca | 56961211752 | #156 Guillaume (0.85) |
| Daniela Tapia Apoderada | Concon | 56982946166 | #94 Daniela Tapia (0.85); #18 apoderada (0.85); #225 Maria Ignacia Apoderada (0.74) |
| Assi Catalan Apoderada | Reñaca | 56985026791 | #217 Assi (0.85); #18 apoderada (0.85); #149 Barbara Apoderada (0.67) |
| Isa Venegas Apoderada | Concon | 56964633042 | #72 Isa Venegas (0.85); #18 apoderada (0.85); #239 Lorena apoderada (0.70) |
| Tamy Apoderada | Concon | 56982511179 | #89 Tamy (0.85); #18 apoderada (0.85); #239 Lorena apoderada (0.73) |
| Claudia (Andres Skinner) | Reñaca | 56997548718 | #152 Claudia Reñaca (0.61); #204 Claudia Vecina (0.61) |
| Maria Jose | Reñaca | 56930562383 | #170 Maria (0.85); #24 Marisa (0.62); #32 Maria Jesus Allende (0.62) |
| Catalina Rivera | Reñaca | 56952157770 | #138 Catalina Arriagada (0.73); #16 Paulina Vega (0.67); #167 Magdalena Marietta (0.61) |
| Paula Apoderada mama Amparo | Reñaca | 56976594622 | #21 Mama amparo (0.85); #108 Paula (0.85); #18 apoderada (0.85) |
| Hans Estay / Carol | Concon  | 56991394911 | #253 Hans Stay (0.72); #95 Vanessa Barros (0.60) |

### Sin coincidencia — ¿cliente nuevo?

| Excel | Comuna | Teléfono |
|---|---|---|
| Leslie de Santa Anna | Las Condes | 56944462325 |
| Pablo Hernandez | Ñuñoa | 56989079205 |
| Katya | Vitacura | 56982026832 |
| Pauli Muñoz | La Reina | 56923963492 |
| Gonzalo Cisterna | Santiago centro | 56993239737 |
| Betsabé Hidalgo Farah | Viña del mar | 56991617870 |

## ⚠️ Colisiones — más de una fila del Excel apunta al mismo cliente ScobyERP

Antes de aplicar cualquier actualización automática, resolver a mano estos casos (no se puede escribir dos teléfonos/direcciones distintos en un mismo cliente):

- **ScobyERP #275 Roberto** — reclamado por 2 filas: CLIENTE PARTICULAR:Roberto; CLIENTE PARTICULAR:Roberto