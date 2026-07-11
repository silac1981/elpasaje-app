# AUDITORIA DE PRICING — El Pasaje 3D Studio
# Generado: 2026-07-10
#
# PROBLEMA: COSTO_KG_DEFAULT en utils/pricing.py = .350/kg
# COSTO REAL segun LEGACY materials (MakerPanda, mayo 2026) = ~0.000-24.000/kg
# Promedio usado en esta auditoria: 1.000/kg (conservador)
#
# Productos propio_3d con peso definido: 82
# PIERDEN PLATA (precio < costo material): 24
# Margen OK a costo real (precio > 4x costo): 12

## TABLA COMPLETA
SKU | Nombre | Peso(g) | PrecioActual | CostoReal | PrecioMin(x4) | Descalce | MargenReal%
--- | ------ | ------- | ------------ | --------- | ------------- | -------- | -----------
OA-MLI-U        | Memory Litophany                    |   3386g | $  35,000 | $  78,216 | $ 312,866 | +$ 277,866 | -123.5% << PIERDE PLATA
OE-BOV-L        | Bandeja Oval L                      |   1925g | $   9,000 | $  44,467 | $ 177,870 | +$ 168,870 | -394.1% << PIERDE PLATA
OA-KIT-P        | Kit Bienvenida Premium              |   2000g | $  45,000 | $  46,200 | $ 184,800 | +$ 139,800 |   -2.7% << PIERDE PLATA
OE-BAS-M        | Bandeja Asimetrica M                |   1538g | $  15,900 | $  35,527 | $ 142,111 | +$ 126,211 | -123.4% << PIERDE PLATA
FSP-003         | Cajita Porta-Figuritas Argentina FI |   1470g | $  10,000 | $  33,957 | $ 135,828 | +$ 125,828 | -239.6% << PIERDE PLATA
FSP-002         | Cajita Porta-Figuritas FIFA 26      |   1470g | $  10,000 | $  33,957 | $ 135,828 | +$ 125,828 | -239.6% << PIERDE PLATA
FSP-001         | Cajita Porta-Figuritas AFA          |   1470g | $  10,000 | $  33,957 | $ 135,828 | +$ 125,828 | -239.6% << PIERDE PLATA
OE-BOV-M        | Bandeja Oval M                      |   1354g | $   6,000 | $  31,277 | $ 125,109 | +$ 119,109 | -421.3% << PIERDE PLATA
FZ-SGB-U        | Soporte Gaming Bicolor              |   1161g | $  12,000 | $  26,819 | $ 107,276 | +$  95,276 | -123.5% << PIERDE PLATA
OE-BDA-U        | Bandeja Damero 35x32                |    900g | $       0 | $  20,790 | $  83,160 | +$  83,160 |    nan% << PIERDE PLATA
OE-BRR-M        | Bandeja Organica Redonda M          |    957g | $   8,000 | $  22,106 | $  88,426 | +$  80,426 | -176.3% << PIERDE PLATA
OA-EEA-U        | Estacion Evolutiva Alto             |    968g | $  10,000 | $  22,360 | $  89,443 | +$  79,443 | -123.6% << PIERDE PLATA
OE-BAS-S        | Bandeja Asimetrica S                |    957g | $   9,900 | $  22,106 | $  88,426 | +$  78,526 | -123.3% << PIERDE PLATA
OE-BOV-S        | Bandeja Oval S                      |    822g | $   3,000 | $  18,988 | $  75,952 | +$  72,952 | -532.9% << PIERDE PLATA
OA-SCP-U        | Soporte Comedero Patita             |    871g | $   9,000 | $  20,120 | $  80,480 | +$  71,480 | -123.6% << PIERDE PLATA
OA-SCH-U        | Soporte Comedero Huesito            |    871g | $   9,000 | $  20,120 | $  80,480 | +$  71,480 | -123.6% << PIERDE PLATA
OA-KIT-E        | Kit Bienvenida Esencial             |    900g | $  15,000 | $  20,790 | $  83,160 | +$  68,160 |  -38.6% << PIERDE PLATA
OA-KIT-C        | Kit Bienvenida Completo             |   1000g | $  28,000 | $  23,100 | $  92,400 | +$  64,400 |   17.5%
OA-EEI-U        | Estacion Evolutiva Inicial          |    774g | $   8,000 | $  17,879 | $  71,517 | +$  63,517 | -123.5% << PIERDE PLATA
OE-SAR-U        | Soporte Aromatico Circular          |    774g | $   8,000 | $  17,879 | $  71,517 | +$  63,517 | -123.5% << PIERDE PLATA
OE-BRR-S        | Bandeja Organica Redonda S          |    629g | $   6,500 | $  14,529 | $  58,119 | +$  51,619 | -123.5% << PIERDE PLATA
M19-TKN-M       | Tirador Knurling M                  |    339g | $   3,500 | $   7,830 | $  31,323 | +$  27,823 | -123.7% << PIERDE PLATA
M19-TKN-S       | Tirador Knurling S                  |    242g | $   2,500 | $   5,590 | $  22,360 | +$  19,860 | -123.6% << PIERDE PLATA
M19-PNE-U       | Porta-notebook ejecutivo            |    380g | $  18,000 | $   8,778 | $  35,112 | +$  17,112 |   51.2%
MEL-PNB-U       | Porta-notebook Melómano             |    350g | $  16,000 | $   8,085 | $  32,340 | +$  16,340 |   49.5%
M19-ORD-U       | Organizador de escritorio modular   |    290g | $  15,000 | $   6,699 | $  26,796 | +$  11,796 |   55.3%
M19-STB-U       | Stand de tablet — consultorio       |    260g | $  14,000 | $   6,006 | $  24,024 | +$  10,024 |   57.1%
AVP-011         | Soporte Monitor Desk                |    180g | $   7,500 | $   4,158 | $  16,632 | +$   9,132 |   44.6%
CT-KAI-001      | Organizador Kaizen                  |    150g | $   5,500 | $   3,465 | $  13,860 | +$   8,360 |   37.0%
M19-BAN-U       | Bandeja de objetos personales       |    220g | $  12,000 | $   5,082 | $  20,328 | +$   8,328 |   57.6%
PD-ORL-001      | Organizador con Logo Lab            |    155g | $   6,000 | $   3,580 | $  14,322 | +$   8,322 |   40.3%
OA-LPG-U        | Llavero Perrito Globo               |     97g | $   1,000 | $   2,240 | $   8,962 | +$   7,962 | -124.1% << PIERDE PLATA
PD-ORG-001      | Organizador Consultorio             |    140g | $   5,200 | $   3,234 | $  12,936 | +$   7,736 |   37.8%
PD-GIF-001      | Gift Set Laboratorio                |    125g | $   4,500 | $   2,887 | $  11,550 | +$   7,050 |   35.8%
COQ-XVA-001     | Kit Quinceanyera                    |    120g | $   4,500 | $   2,772 | $  11,088 | +$   6,588 |   38.4%
CT-RPI-001      | Case Raspberry Pi 5                 |    120g | $   4,500 | $   2,772 | $  11,088 | +$   6,588 |   38.4%
OA-GTG-U        | Guardian Tag QR Emergencia          |     77g | $     800 | $   1,778 | $   7,114 | +$   6,314 | -122.3% << PIERDE PLATA
CT-ORG-001      | Organizador Anti-Estatico           |    110g | $   4,200 | $   2,541 | $  10,164 | +$   5,964 |   39.5%
AVP-005         | Organizador Banco Personal          |    120g | $   5,500 | $   2,772 | $  11,088 | +$   5,588 |   49.6%
CT-GAB-001      | Gabinete Microelectronica           |    100g | $   3,800 | $   2,310 | $   9,240 | +$   5,440 |   39.2%
PD-SER-001      | Soporte Seringa                     |    100g | $   3,800 | $   2,310 | $   9,240 | +$   5,440 |   39.2%
FZ-ORC-001      | Organizador Cancha                  |     95g | $   3,900 | $   2,194 | $   8,778 | +$   4,878 |   43.7%
CT-CUB-001      | Cubo Infinito Magnetico             |     90g | $   3,800 | $   2,079 | $   8,316 | +$   4,516 |   45.3%
AVP-008         | Torre de Control                    |    110g | $   5,800 | $   2,541 | $  10,164 | +$   4,364 |   56.2%
AVP-013         | Hub Organizador USB                 |     95g | $   4,500 | $   2,194 | $   8,778 | +$   4,278 |   51.2%
PD-MUE-001      | Muestrero Medico                    |     75g | $   2,800 | $   1,732 | $   6,930 | +$   4,130 |   38.1%
CT-SIM-001      | Soporte Instrumento Medicion        |     70g | $   2,400 | $   1,617 | $   6,468 | +$   4,068 |   32.6%
FZ-TRO-001      | Trofeo Mini                         |     65g | $   2,200 | $   1,501 | $   6,006 | +$   3,806 |   31.8%
AVP-009         | Placa Analista Senior               |     90g | $   4,800 | $   2,079 | $   8,316 | +$   3,516 |   56.7%
AVP-001         | Rampa-Safe                          |     85g | $   4,500 | $   1,963 | $   7,854 | +$   3,354 |   56.4%
PD-PAS-001      | Porta-Pastillas Semanal             |     50g | $   1,800 | $   1,155 | $   4,620 | +$   2,820 |   35.8%
COQ-MON-002     | Monedero Silk Coquette              |     60g | $   2,800 | $   1,386 | $   5,544 | +$   2,744 |   50.5%
AVP-006         | Dock Checklist                      |     75g | $   4,200 | $   1,732 | $   6,930 | +$   2,730 |   58.8%
AVP-002         | Mate-Carro                          |     70g | $   3,800 | $   1,617 | $   6,468 | +$   2,668 |   57.4%
FZ-CAP-001      | Cap-Hanger Pro                      |     45g | $   1,800 | $   1,039 | $   4,158 | +$   2,358 |   42.2%
MEL-ADH-U       | Audiophile Desk Hub                 |    480g | $  42,000 | $  11,088 | $  44,352 | +$   2,352 |   73.6%
AVP-012         | Portacelular 360                    |     65g | $   3,800 | $   1,501 | $   6,006 | +$   2,206 |   60.5%
AVP-007         | Organizador Fuselaje                |     60g | $   3,500 | $   1,386 | $   5,544 | +$   2,044 |   60.4%
COQ-CAJ-001     | Cajita Corazon                      |     45g | $   2,200 | $   1,039 | $   4,158 | +$   1,958 |   52.7%
AVP-010         | Portabotella Aero                   |     55g | $   3,200 | $   1,270 | $   5,082 | +$   1,882 |   60.3%
FZ-GMR-001      | Aplique Gamer                       |     30g | $   1,200 | $     693 | $   2,772 | +$   1,572 |   42.2%
FZ-PFX-001      | Parche Flexible                     |     25g | $     900 | $     577 | $   2,310 | +$   1,410 |   35.8%
AVP-004         | Porta-Credencial Pro                |     45g | $   2,800 | $   1,039 | $   4,158 | +$   1,358 |   62.9%
AVP-003         | Clip Seguridad EPP                  |     35g | $   2,200 | $     808 | $   3,234 | +$   1,034 |   63.2%
MEL-HWS-U       | Heavyweight Stabilizer              |    335g | $  30,000 | $   7,738 | $  30,954 | +$     954 |   74.2%
COQ-MON-001     | Mono Textil Silk                    |     22g | $   1,500 | $     508 | $   2,032 | +$     532 |   66.1%
FZ-NUM-001      | Numero de Camiseta                  |     12g | $     600 | $     277 | $   1,108 | +$     508 |   53.8%
COQ-PRE-001     | Prendedor Floral                    |     18g | $   1,400 | $     415 | $   1,663 | +$     263 |   70.3%
COQ-LLA-001     | Llavero Peonia                      |     15g | $   1,200 | $     346 | $   1,386 | +$     186 |   71.1%
COQ-ARG-001     | Argolla Coquette                    |     20g | $   1,800 | $     462 | $   1,848 | +$      48 |   74.3%
VC-PPT-U        | Porta-pelotas tenis (3u)            |     90g | $  10,000 | $   2,079 | $   8,316 | +$  -1,683 |   79.2%
MEL-SAU-U       | Stand armónica y ukelele            |    140g | $  15,000 | $   3,234 | $  12,936 | +$  -2,064 |   78.4%
VC-PRA-U        | Porta-raqueta de pared premium      |    150g | $  16,000 | $   3,465 | $  13,860 | +$  -2,140 |   78.3%
VC-FJG-U        | Fletcher Jig 360°                   |    120g | $  15,000 | $   2,772 | $  11,088 | +$  -3,912 |   81.5%
M19-FCO-U       | Fidget corporal — Reuniones         |     28g | $   6,500 | $     646 | $   2,587 | +$  -3,912 |   90.0%
M19-FDE-S       | Fidget de escritorio — Botones      |     45g | $   8,500 | $   1,039 | $   4,158 | +$  -4,341 |   87.8%
M19-FDE-T       | Fidget de escritorio — Texturas     |     38g | $   8,000 | $     877 | $   3,511 | +$  -4,488 |   89.0%
M19-FDE-R       | Fidget de escritorio — Rueda        |     52g | $   9,500 | $   1,201 | $   4,804 | +$  -4,695 |   87.4%
VC-QPR-U        | Quiver Pro — soporte arco + 12 flec |    380g | $  42,000 | $   8,778 | $  35,112 | +$  -6,887 |   79.1%
MEL-NPP-U       | Now Playing Premium                 |    160g | $  23,000 | $   3,696 | $  14,784 | +$  -8,216 |   83.9%
MEL-ISQ-U       | Iso-Spike Quartet — 4 spikes        |    180g | $  27,000 | $   4,158 | $  16,632 | +$ -10,367 |   84.6%
MEL-VSO-U       | Vinyl Sommelier — 27 divisores A-Z+ |    420g | $  67,000 | $   9,702 | $  38,808 | +$ -28,191 |   85.5%

## DECISION PENDIENTE (Comite antes de Fase C)
1. Verificar con Fer: cuanto costo el ultimo rollo? (ticket MakerPanda)
2. Si ~0.000/kg es correcto: actualizar COSTO_KG_DEFAULT y repreciar catalogo
3. Productos mas urgentes: OE-BOV-* (bandejas), OA-MLI-U (litofania), FSP-* (ya en interno)
4. Regla: precio < 2x costo material = venta a perdida. Hoy hay 24 productos en esa zona.