import matplotlib.pyplot as plt
import numpy as np

freqs = [ 1.        , 1.01010101 ,1.02020202 ,1.03030303 ,1.04040404, 1.05050505 ,
          1.06060606, 1.07070707 ,1.08080808 ,1.09090909 ,1.1010101 , 1.11111111 ,
          1.12121212, 1.13131313 ,1.14141414 ,1.15151515 ,1.16161616, 1.17171717 ,
          1.18181818, 1.19191919 ,1.2020202  ,1.21212121 ,1.22222222, 1.23232323 ,
          1.24242424, 1.25252525 ,1.26262626 ,1.27272727 ,1.28282828, 1.29292929 ,
          1.3030303 , 1.31313131 ,1.32323232 ,1.33333333 ,1.34343434, 1.35353535 ,
          1.36363636, 1.37373737 ,1.38383838 ,1.39393939 ,1.4040404 , 1.41414141 ,
          1.42424242, 1.43434343 ,1.44444444 ,1.45454545 ,1.46464646, 1.47474747 ,
          1.48484848, 1.49494949 ,1.50505051 ,1.51515152 ,1.52525253, 1.53535354 ,
          1.54545455, 1.55555556 ,1.56565657 ,1.57575758 ,1.58585859, 1.5959596  ,
          1.60606061, 1.61616162 ,1.62626263 ,1.63636364 ,1.64646465, 1.65656566 ,
          1.66666667, 1.67676768 ,1.68686869 ,1.6969697  ,1.70707071, 1.71717172 ,
          1.72727273, 1.73737374 ,1.74747475 ,1.75757576 ,1.76767677, 1.77777778 ,
          1.78787879, 1.7979798  ,1.80808081 ,1.81818182 ,1.82828283, 1.83838384 ,
          1.84848485, 1.85858586 ,1.86868687 ,1.87878788 ,1.88888889, 1.8989899  ,
          1.90909091, 1.91919192 ,1.92929293 ,1.93939394 ,1.94949495, 1.95959596 ,
          1.96969697, 1.97979798 ,1.98989899 ,2.        ]          
# Sun measured at approx 18 deg elevation
suntotpows = [2785.6330876946449, 1977.1466615200043, 1589.494863897562, 1542.7959198653698, 1557.8172065913677, 1735.6908074915409, 2129.2754965126514, 2353.7702390253544, 1972.3789359033108, 2520.4937805235386, 1282.1320186555386, 1237.6904610097408, 1405.4985212385654, 1943.0715529024601, 2858.5671704411507, 3274.8328270316124, 3564.6992583870888, 3669.2628258466721, 4586.2290814518929, 5375.4824217557907, 6455.6713807582855, 7866.3508347272873, 10485.52419924736, 10127.730884552002, 8344.336953997612, 6466.1049537658691, 5280.8985623121262, 5250.1298352479935, 5314.5343601703644, 6038.8015081882477, 6214.5116136074066, 5930.2830632925034, 4645.7253813147545, 4158.2600346207619, 3803.7233927249908, 3759.6277379989624, 4292.0511005520821, 4624.2467453479767, 5030.3273301124573, 4295.354663848877, 3536.6770436167717, 2730.3309785723686, 2416.423579454422, 2336.9050691723824, 2094.2399448156357, 2495.4593307971954, 2395.4762416183949, 1968.5652746260166, 1370.5805124044418, 1260.2253520190716, 1202.7231127619743, 1206.297066539526, 1361.7773389518261, 1552.519161939621, 1828.438550055027, 1775.8439630866051, 1582.4709193408489, 1556.387759834528, 832.66799978911877, 588.73582801222801, 651.42778930813074, 699.11164103448391, 619.32082325220108, 433.08832363039255, 322.50797021389008, 314.95811840891838, 374.19519168138504, 432.44684907793999, 443.08514755964279, 460.69489664584398, 455.19357943534851, 397.53214629739523, 351.27304589003325, 273.39031756296754, 232.59308376535773, 228.33922612667084, 204.66613719984889, 166.71212916448712, 138.45455680601299, 111.94994743354619, 739.86359599977732, 405.20963317155838, 72.816294245421886, 74.506069138646126, 68.830861670896411, 82.954384192824364, 83.197337875142694, 63.829409923404455, 58.214999719522893, 53.334227626211941, 47.608955097384751, 42.91682996135205, 45.085554989986122, 48.646714971400797, 51.167791061103344, 49.396051414310932, 47.978826837614179, 41.228333038277924, 38.292552176862955, 41.856090572662652]

# Measured at zenith, should be far enough from the sun to be a good zero level.
zenithtotpows = [1943.6411018371582, 1482.5802601575851, 1151.7467851042747, 1244.6229656487703, 1302.7019702196121, 2602.2718475461006, 3785.8905768990517, 5145.2179720401764, 4183.0708646774292, 2542.1989408433437, 1144.5393799543381, 854.80862618982792, 837.97461956739426, 995.92484059929848, 1162.1792143434286, 1322.1115420460701, 1325.1730933338404, 1100.4929715096951, 1139.4452214539051, 1075.5127658247948, 1099.5105756223202, 1168.342494815588, 1375.2484279870987, 1434.9314380884171, 1360.0316359996796, 1077.9956717938185, 908.95068320631981, 896.39201503992081, 983.52154520153999, 1140.434398189187, 1265.9182561039925, 1214.5917905569077, 924.46561880409718, 853.2023981064558, 744.55698086321354, 686.73946462571621, 789.24938863515854, 847.71881730854511, 855.3574857711792, 757.26768906414509, 606.07812813669443, 465.58327329158783, 437.5682440251112, 412.08593615144491, 364.77455784380436, 472.19709119945765, 516.77393741905689, 485.4437377974391, 460.91582728177309, 457.36334832012653, 479.17593301087618, 347.65261828154325, 294.29305405914783, 258.27139937877655, 265.72725412622094, 356.57809749990702, 215.72405383735895, 226.11679937317967, 162.22952026873827, 164.5044366940856, 219.81728319451213, 340.53004756569862, 547.15641456842422, 518.41886118799448, 265.53626054897904, 182.17695025354624, 127.92363779060543, 125.63371352106333, 123.76056421920657, 118.65346656739712, 117.87782165594399, 115.08676435798407, 146.01153200492263, 175.86969291046262, 295.32032546401024, 405.0511381700635, 727.21525095403194, 154.49599220976233, 104.65012673847377, 82.725409341976047, 324.13157342374325, 382.79943937063217, 73.37178741581738, 134.08102109283209, 90.209561819210649, 206.97617258131504, 422.87319120764732, 454.66064346581697, 356.65183033794165, 165.66637360677123, 109.50364381447434, 57.247826880775392, 63.019179145805538, 66.039286904036999, 72.274781942367554, 74.631841246038675, 102.46883722022176, 156.93706633150578, 220.66997799277306, 193.30993343517184]

suntotpows=np.array(suntotpows)
zenithtotpows = np.array(zenithtotpows)

plt.plot(freqs, suntotpows)
plt.plot(freqs, zenithtotpows)
plt.legend(['The Sun at 18 deg el.', 'Same on Zenith (background)'])
plt.title('SALSA Vale, 2 second measurements for 100 freq. points')
plt.xlabel('Frequency[GHz]')
plt.ylabel('Amp. (average over 2MHz) [arbitraty scale]')
plt.xlim([1, 2])
plt.savefig('both.png', dpi=300, bbox_inches='tight')
plt.figure()
plt.plot(freqs, suntotpows/zenithtotpows)
plt.legend(['The Sun / Zenith'])
plt.title('SALSA Vale, 2 second measurements for 100 freq. points')
plt.xlabel('Frequency[GHz]')
plt.ylabel('The Sun / Zenith, i.e. approx SNR')
plt.xlim([1.3, 2])
plt.savefig('snr.png', dpi=300, bbox_inches='tight')
plt.show()
