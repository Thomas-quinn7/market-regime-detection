# Data manifest

Written by `examples/data_manifest.py` on pc-lanes at 2026-10-18 06:27Z, repo at a53cbf5. 101 files.

Holdout column: the holdouts whose reproduction (`examples/reproduce_holdout.py`) read the file,
from `docs/results/reproductions/*/provenance.json`; "-" means no reproduction read it. mtimes are
on this host: files copied here from the laptop on 2026-10-17 carry the copy time, so only files
first written on this host (the ETF caches and checkpoints) date their download or computation.
"git" says whether the file is committed; the rest are local caches (see .gitignore).

| file | sha256 | bytes | mtime (UTC) | holdouts | freeze commit | git |
|---|---|---|---|---|---|---|
| `data/BIL_2000-01-01_2017-12-31.csv` | `e76d940576b29c65b4669faecc8112813f06981951d039cd222e79c8e58327ec` | 76830 | 2026-10-18 06:21:01Z | - | - | no |
| `data/BIL_2005-01-01_2023-12-31.csv` | `cbc280d4e6bcea95cfdbd9b46eff6d8115373db162899b323e70e02d956ba9a8` | 124548 | 2026-10-17 14:44:42Z | - | - | no |
| `data/DBC_2000-01-01_2017-12-31.csv` | `e01ab7048a50cba4b0947694d132218110c9ffb2c19d6c232204086c172173dd` | 88917 | 2026-10-18 06:21:01Z | - | - | no |
| `data/DGS10_fredgraph.csv` | `624f2a18b0c5642c72dbf8c58cf54b9dcee50d7d8cb3b7809b9416dabd09dd55` | 268999 | 2026-10-14 11:55:45Z | stock_bond | 53b50c6 | yes |
| `data/DJI_2000-01-01_2026-10-13.csv` | `de065b250814b446da7417ddf9c16815f62361d4cd8d45395c7618e6fb3f63dc` | 183050 | 2026-10-17 14:44:42Z | cross_index | 963cb5e | no |
| `data/EEM_2000-01-01_2017-12-31.csv` | `bed5a74cb3583f4e9f98aa7d78268934e3865a3ce8e29af775e5a82881679bfe` | 109320 | 2026-10-18 06:20:59Z | - | - | no |
| `data/EEM_2000-01-01_2026-10-13.csv` | `2ee15313ec37a6161cc8861273aeb0502e20fba8c8a70f21b565729ba22f6030` | 173694 | 2026-10-14 12:17:28Z | etf | da0cf0f | no |
| `data/EFA_2000-01-01_2017-12-31.csv` | `3f9c045333abfa72b584134b2f38ef484ac9b96367a08078fb2d523220d7976f` | 120658 | 2026-10-18 06:20:59Z | - | - | no |
| `data/EWZ_2000-01-01_2026-10-13.csv` | `aa788cdbac3e32c079defba9f1466945ad2d379112c3b2d5ac796cbf08ce7f7d` | 194403 | 2026-10-14 12:20:50Z | etf | da0cf0f | no |
| `data/GLD_2000-01-01_2017-12-31.csv` | `591033c7a891d7c1232954e460f6376f2a82a61ce627ce18478f333f5ebe6567` | 95433 | 2026-10-18 06:21:00Z | - | - | no |
| `data/GLD_2000-01-01_2026-10-13.csv` | `0e8f882dd0ab9792900c284471f0b9ca456aef706428ce5ca45894fb82f6544c` | 159554 | 2026-10-14 12:14:55Z | etf | da0cf0f | no |
| `data/GSPC_1927-12-30_2023-12-31.csv` | `ec0c0d92580fe53be0191585398fa1b5a4e27c44dd78dc70a377e1c5655c2467` | 716607 | 2026-10-17 14:44:42Z | - | - | no |
| `data/GSPC_1962-01-01_2023-12-31.csv` | `7e3273e9bef1c9d1e2bf4428591f3e9a120b66f8b9d613579a52ec40067b0c23` | 461637 | 2026-10-17 14:44:42Z | stock_bond | 53b50c6 | no |
| `data/GSPC_1990-01-01_2004-12-31.csv` | `db18ed2cf1125907f9251e1074aa3a4d61c31c7dd45b7c9247b83f08ce7b7978` | 112089 | 2026-10-17 14:44:42Z | vix_early | 3fea6a7 | no |
| `data/GSPC_2000-01-01_2009-12-31.csv` | `1f39e4f4565c9dabbf48c6f8e0aa3058bfce9a57725104c9787c735bd0c9f394` | 74704 | 2026-10-17 14:44:42Z | - | - | no |
| `data/GSPC_2000-01-01_2023-12-31.csv` | `ebfbfc6b2ff5368b5a1a57dcedd758e6bfd2fb677d47e1a8fb08eddcf1b95106` | 176961 | 2026-10-14 11:55:53Z | - | - | no |
| `data/GSPC_2000-01-01_2024-01-01.csv` | `ebfbfc6b2ff5368b5a1a57dcedd758e6bfd2fb677d47e1a8fb08eddcf1b95106` | 176961 | 2026-10-14 11:57:52Z | - | - | no |
| `data/GSPC_2005-01-01_2023-12-31.csv` | `5da530b409c37d50c0102ce8f669777b290cbcaa730f49d206901c368a924b2e` | 139578 | 2026-10-17 14:44:42Z | - | - | no |
| `data/GSPC_2005-01-01_2026-10-13.csv` | `bf19a9cb5734947ae78bd12c6aa204b2bd9ce52b9dcb363629999e26963ff4c4` | 158945 | 2026-10-17 14:44:42Z | vix_recent | 3fea6a7 | no |
| `data/GSPC_2015-01-01_2020-12-31.csv` | `36d89ec8c116a6fc82c0a43b5fb9e52db99d32d8f3275ea6cc3e299da01d91de` | 43705 | 2026-10-17 14:44:42Z | - | - | no |
| `data/HYG_2000-01-01_2017-12-31.csv` | `32ecf5cc301284e9852bc106f5a37f8ca8944408d3fcd35d8becf9d861ead40b` | 79120 | 2026-10-18 06:21:00Z | - | - | no |
| `data/IEF_2000-01-01_2017-12-31.csv` | `ce2e38ab2598ce0696f160016bd7fae5ac99b61d8594ab5590eeb8dbfe67361d` | 112595 | 2026-10-18 06:20:59Z | - | - | no |
| `data/IEF_2005-01-01_2023-12-31.csv` | `a690e809ce28599e86c2a1c5e606b8114bb8b6566d717b696e66d9af43cedb80` | 143144 | 2026-10-17 14:44:42Z | - | - | no |
| `data/LQD_2000-01-01_2017-12-31.csv` | `07b2c97001fa81fef5b2f1ac9dc67ddaf59a3ea3987216e9144361f9c90703d4` | 112712 | 2026-10-18 06:21:00Z | - | - | no |
| `data/NDX_2000-01-01_2026-10-13.csv` | `5eb8b56f209a42d3ec4d99ab5ec6b7524e275a24cd928a55eb9a774d94eabaf6` | 192622 | 2026-10-17 14:44:42Z | cross_index | 963cb5e | no |
| `data/RUT_2000-01-01_2026-10-13.csv` | `f3912a01475da2a3b79a897f31467c5e96001b5ab6b8b3be62587f3b42a3ff11` | 197946 | 2026-10-17 14:44:42Z | cross_index | 963cb5e | no |
| `data/SKEW_2005-01-01_2023-12-31.csv` | `39dd2036456f277d4979e48f0ec00d63a8e4bfb92e5e9b95fc487496e0a9595d` | 143246 | 2026-10-17 14:44:42Z | - | - | no |
| `data/SPY_2000-01-01_2017-12-31.csv` | `f73927e4258f43e33bba24df20cd94272d737fd6932844de23dff7bd36be4cde` | 131803 | 2026-10-18 06:20:59Z | - | - | no |
| `data/SPY_2005-01-01_2023-12-31.csv` | `b45532b4cc2f0e8a2e0e52e6b380a3f25125671f4ac87ddd016c646c3b0cbb57` | 144458 | 2026-10-17 14:44:42Z | - | - | no |
| `data/TIP_2000-01-01_2017-12-31.csv` | `622fd7fc03277fdacdddb1ba400c815415422df9907469d5f0e40d2e08f715c4` | 102539 | 2026-10-18 06:21:00Z | - | - | no |
| `data/TLT_2000-01-01_2017-12-31.csv` | `8a2d927a7c2929273343e37ef5afc0a678ef6bf938bd6ed6abb0a5f716738fd7` | 112635 | 2026-10-18 06:21:00Z | - | - | no |
| `data/USO_2000-01-01_2026-10-13.csv` | `53a31cae66a44c0bef0d813bef58cc0c72372e0dbde1dfcf20212d5cc9a3049f` | 147406 | 2026-10-14 12:12:16Z | etf | da0cf0f | no |
| `data/VIX3M_2005-01-01_2023-12-31.csv` | `3ce4fccf06c3eef24a5b16c07486f95174ed44ea2669381d18d12159f7fbab75` | 132336 | 2026-10-17 14:44:42Z | - | - | no |
| `data/VIX6M_2005-01-01_2023-12-31.csv` | `08555dc9bbcf538e189a731b188c28809ea4d844ec2113b6d310a626f2c2c2ea` | 120980 | 2026-10-17 14:44:42Z | - | - | no |
| `data/VIX9D_2005-01-01_2023-12-31.csv` | `f5026ed483019d41b9ac23c96909dc1a16454ccc1e9f5293b9094791cfe87556` | 98489 | 2026-10-17 14:44:42Z | - | - | no |
| `data/VIX_1990-01-01_2004-12-31.csv` | `e29461289a03b336d4c414f5fd0e247ec3a167f1cae2196139bf0beffc30a126` | 113620 | 2026-10-17 14:44:42Z | vix_early | 3fea6a7 | no |
| `data/VIX_2000-01-01_2023-12-31.csv` | `d55e1cb13a31eef0f8d7132a53d1179c36f143d46a0e2f25b4129b9a4a6ff16b` | 181738 | 2026-10-14 11:55:54Z | - | - | no |
| `data/VIX_2005-01-01_2023-12-31.csv` | `01bb0a637798f6bec7cd191dd72b127c61f7268b663a45f44608ac9b40e036fe` | 144251 | 2026-10-17 14:44:42Z | - | - | no |
| `data/VIX_2005-01-01_2026-10-13.csv` | `a48f07522f2f4902663db917d6af3849ba1d7ac615a501305e1e6f9b10dda20d` | 165346 | 2026-10-17 14:44:42Z | vix_recent | 3fea6a7 | no |
| `data/VNQ_2000-01-01_2017-12-31.csv` | `3ac8e1b3890094d59ed5e87f13a805785b308a647dbfc577f3ddb353308757a3` | 98094 | 2026-10-18 06:21:01Z | - | - | no |
| `data/VVIX_2005-01-01_2023-12-31.csv` | `4c980c2970f0ecc0eb835d4e2b92c028159877cb96a367d54df8c722233ab18b` | 126432 | 2026-10-17 14:44:42Z | - | - | no |
| `data/XLB_2005-01-01_2023-12-31.csv` | `5846c2f6b4a514d6013063efc447ee404f971ffbcc046b36e8db88b84e48c562` | 145929 | 2026-10-17 14:44:42Z | - | - | no |
| `data/XLE_2005-01-01_2023-12-31.csv` | `74f8fad9087ea17503ff29e370751a2ce4960319fb6219c9666303b3e91205b3` | 146220 | 2026-10-17 14:44:42Z | - | - | no |
| `data/XLF_2005-01-01_2023-12-31.csv` | `5b8735bef60294d3a2816dda96449c0ad1a3b360aac61f9daa878eca45f31b90` | 145628 | 2026-10-17 14:44:42Z | - | - | no |
| `data/XLI_2005-01-01_2023-12-31.csv` | `01214312e41a67d45ddd669a76d8d6630267b2bfd9bf5534a51fb8f80f49c6f3` | 144718 | 2026-10-17 14:44:42Z | - | - | no |
| `data/XLK_2005-01-01_2023-12-31.csv` | `5be73a5e598f4f1a19c83ea866368a4ed2c67099113ba865df9e78ac045ec4c7` | 144650 | 2026-10-17 14:44:42Z | - | - | no |
| `data/XLP_2005-01-01_2023-12-31.csv` | `3bd15914c8c5ee9ffaaf9303c56696f42cf755925176bf0db48a717a68318b25` | 145276 | 2026-10-17 14:44:42Z | - | - | no |
| `data/XLU_2005-01-01_2023-12-31.csv` | `b8deaed3b5138b7938ac112f97ad11ea097e613ba3d6767dde009d22f5739159` | 145600 | 2026-10-17 14:44:42Z | - | - | no |
| `data/XLV_2005-01-01_2023-12-31.csv` | `0a59748bbf64d7046340f96780aa7ea9d711059e5f5c4ade50f6a5dafcf39bef` | 145254 | 2026-10-17 14:44:42Z | - | - | no |
| `data/XLY_2005-01-01_2023-12-31.csv` | `10aecc33a66e2d6b3260eba3b405f4b3e73b0ca102bca277d7564d6a7a67f060` | 145184 | 2026-10-17 14:44:42Z | - | - | no |
| `data/checkpoints/msgarch_credit/brazil_ewz__garch__2026-10-12__6599.csv` | `9c4ac2c4139005d194b05e4390f58024d84f5f4a895b1147bf718bd9dba38107` | 173060 | 2026-10-14 12:21:37Z | etf | da0cf0f | no |
| `data/checkpoints/msgarch_credit/brazil_ewz__garch__2026-10-12__6599.params.csv` | `b6b8039668d77771b16314bc97e506b4d9bb832aaa154c3fed995b22b136a82c` | 11918 | 2026-10-14 12:21:37Z | etf | da0cf0f | no |
| `data/checkpoints/msgarch_credit/brazil_ewz__hmm__2026-10-12__6599.csv` | `e0cf445372602c724647e29a052f0f65bc3482dec239dca1ce98985ffa958593` | 290821 | 2026-10-14 12:21:35Z | etf | da0cf0f | no |
| `data/checkpoints/msgarch_credit/brazil_ewz__ms_garch__2026-10-12__6599.csv` | `c876f13a85d292929d00b22fee8c0cc6f961e2f13d3a3b68614cf83f67418f12` | 273528 | 2026-10-14 12:25:00Z | etf | da0cf0f | no |
| `data/checkpoints/msgarch_credit/brazil_ewz__ms_garch__2026-10-12__6599.params.csv` | `f4b414aaf4858eb0c4cc32ab31d13717882a1d2a3885a669e03fab62b08b4bfb` | 25124 | 2026-10-14 12:25:00Z | etf | da0cf0f | no |
| `data/checkpoints/msgarch_credit/crude_oil_uso__garch__2026-10-12__5158.csv` | `a6e31883483e267328dbf20e60120372fecad9b6a6086b40226e757bd644cb8b` | 130442 | 2026-10-14 12:12:45Z | etf | da0cf0f | no |
| `data/checkpoints/msgarch_credit/crude_oil_uso__garch__2026-10-12__5158.params.csv` | `4155ca2a79a75981c559026808f22454d3ab4ed93d73c0b806a3de3504e19dd7` | 9153 | 2026-10-14 12:12:45Z | etf | da0cf0f | no |
| `data/checkpoints/msgarch_credit/crude_oil_uso__hmm__2026-10-12__5158.csv` | `7980601324921e848dd33b774ac98918c22cedde8d13679a487d8678769fa0f9` | 219603 | 2026-10-14 12:12:44Z | etf | da0cf0f | no |
| `data/checkpoints/msgarch_credit/crude_oil_uso__ms_garch__2026-10-12__5158.csv` | `b19c2d9af3cb44fbf8c8935ed2575df0fbc7c589eed5c571b5d5429b047b9f3f` | 217200 | 2026-10-14 12:14:54Z | etf | da0cf0f | no |
| `data/checkpoints/msgarch_credit/crude_oil_uso__ms_garch__2026-10-12__5158.params.csv` | `f726525618d3f5471474daf340c3fc17e6d2f46ab40de5c26bd11dcbab78d468` | 18623 | 2026-10-14 12:14:54Z | etf | da0cf0f | no |
| `data/checkpoints/msgarch_credit/emerging_markets_eem__garch__2026-10-12__5911.csv` | `9d79feb19c454dc4d565997342c9bdbfd5f4f68de7b88f3206edcb1511bae70a` | 153209 | 2026-10-14 12:18:03Z | etf | da0cf0f | no |
| `data/checkpoints/msgarch_credit/emerging_markets_eem__garch__2026-10-12__5911.params.csv` | `2b49d8c461173ebf2a14c39d35ab220760db9597e6d7b75ff6222bc8adf322de` | 10551 | 2026-10-14 12:18:03Z | etf | da0cf0f | no |
| `data/checkpoints/msgarch_credit/emerging_markets_eem__hmm__2026-10-12__5911.csv` | `f4c22ab6235f8393fca4fb7124e387a8f06854abce80ea2e9453ddf0340abf1f` | 259107 | 2026-10-14 12:18:02Z | etf | da0cf0f | no |
| `data/checkpoints/msgarch_credit/emerging_markets_eem__ms_garch__2026-10-12__5911.csv` | `009c040ef43ed11362866d3014d8406f6e60bbcb87eef37dcfa73fc123d513b9` | 253177 | 2026-10-14 12:20:49Z | etf | da0cf0f | no |
| `data/checkpoints/msgarch_credit/emerging_markets_eem__ms_garch__2026-10-12__5911.params.csv` | `36fc120b77ecd24bf1d00cef0927e08022f8ea00ae95b68ed07f3b7713cae0c3` | 21794 | 2026-10-14 12:20:49Z | etf | da0cf0f | no |
| `data/checkpoints/msgarch_credit/gold_gld__garch__2026-10-12__5507.csv` | `762bf544f2cdd73e3d7d6403e785047bbf786a3b2857b369f56c25d5ae6fc7a5` | 141574 | 2026-10-14 12:15:26Z | etf | da0cf0f | no |
| `data/checkpoints/msgarch_credit/gold_gld__garch__2026-10-12__5507.params.csv` | `08830838488f70be9375e6209218ca0ee3565c68b587d1e70bf3ba8914613695` | 9942 | 2026-10-14 12:15:26Z | etf | da0cf0f | no |
| `data/checkpoints/msgarch_credit/gold_gld__hmm__2026-10-12__5507.csv` | `4b9a2b3ed1d30329862e908c985be94da97ed5f3c7381ab061c9929f23c0fcf3` | 236767 | 2026-10-14 12:15:24Z | etf | da0cf0f | no |
| `data/checkpoints/msgarch_credit/gold_gld__ms_garch__2026-10-12__5507.csv` | `5963c8b1e8def805a714489e091ef95c4e081ebf2061300ad9d28c242c76585b` | 234801 | 2026-10-14 12:17:27Z | etf | da0cf0f | no |
| `data/checkpoints/msgarch_credit/gold_gld__ms_garch__2026-10-12__5507.params.csv` | `91df92b34d490db2e5178f736e542e047cdd0c9652670ac9f9832c2d0e8903c6` | 20486 | 2026-10-14 12:17:27Z | etf | da0cf0f | no |
| `data/checkpoints/msgarch_credit/s_p_500_development__garch__2023-12-31__6036.csv` | `ca1ac4374932c42c234924b25290bbb7678ee2662bc32657d8af6301d0395d94` | 157421 | 2026-10-14 11:57:07Z | etf (frozen-run checkpoints) | da0cf0f | no |
| `data/checkpoints/msgarch_credit/s_p_500_development__garch__2023-12-31__6036.params.csv` | `5b6669b2fd6682a189c69c6c1d9273e205f9b83d6923f9d3032ad0d30e1fbd3c` | 10267 | 2026-10-14 11:57:07Z | etf (frozen-run checkpoints) | da0cf0f | no |
| `data/checkpoints/msgarch_credit/s_p_500_development__hmm__2023-12-31__6036.csv` | `e4967ec7e0bae745c2362f306891c7c7d2eb63f3cabcfc13a6400e73acf9e2a7` | 263845 | 2026-10-14 11:57:35Z | etf (frozen-run checkpoints) | da0cf0f | no |
| `data/checkpoints/msgarch_credit/s_p_500_development__ms_garch__2023-12-31__6036.csv` | `cc31f787d3b8f749066e4220f11446395df0887ddd2742767ca09d44bec211ba` | 258130 | 2026-10-14 11:58:56Z | etf (frozen-run checkpoints) | da0cf0f | no |
| `data/checkpoints/msgarch_credit/s_p_500_development__ms_garch__2023-12-31__6036.params.csv` | `a64db82b2c24cb27c357c9a5e5a0f5b5c65d380eb7d0f2ee42d5f389a3c1b110` | 22814 | 2026-10-14 11:58:56Z | etf (frozen-run checkpoints) | da0cf0f | no |
| `data/checkpoints/msgarch_credit/s_p_500_development__ms_garch_normal__2023-12-31__6036.csv` | `f725c1e8a6bc8ba22e81c1187bb838aacc4915be2bf70096b275b1ae850e407c` | 257959 | 2026-10-14 11:57:53Z | etf (frozen-run checkpoints) | da0cf0f | no |
| `data/checkpoints/msgarch_credit/s_p_500_development__ms_garch_normal__2023-12-31__6036.params.csv` | `ce7c7e08165086cf096df5f57abdfff534aefd0845b4ef1222b0dd8194ec2f96` | 20426 | 2026-10-14 11:57:53Z | etf (frozen-run checkpoints) | da0cf0f | no |
| `data/checkpoints/msgarch_credit/s_p_500_development__ms_garch_t_stay_0_5__2023-12-31__6036.csv` | `14439b09258ac0e471121136532e1e9f92f6acc83fff34d558ffe50d92cec681` | 259513 | 2026-10-14 11:58:51Z | etf (frozen-run checkpoints) | da0cf0f | no |
| `data/checkpoints/msgarch_credit/s_p_500_development__ms_garch_t_stay_0_5__2023-12-31__6036.params.csv` | `8707b77e3a46e90d6441cd2ff68f7afb872406e6e79b62dbf4db5157a7e3b0a6` | 22635 | 2026-10-14 11:58:51Z | etf (frozen-run checkpoints) | da0cf0f | no |
| `data/checkpoints/msgarch_credit/s_p_500_dry_run_development_data__garch__2023-12-31__6036.csv` | `6a6c5f63e6ae2b3791cc78d660f966cb756b975a091bcd5c490b6619fd15af69` | 157372 | 2026-10-14 12:07:21Z | etf (frozen-run checkpoints) | da0cf0f | no |
| `data/checkpoints/msgarch_credit/s_p_500_dry_run_development_data__garch__2023-12-31__6036.params.csv` | `a4e3b57e168dedd308cf4a6a95d5f43be491cd55a81a5cbe089a9548170481b3` | 10312 | 2026-10-14 12:07:21Z | etf (frozen-run checkpoints) | da0cf0f | no |
| `data/checkpoints/msgarch_credit/s_p_500_dry_run_development_data__hmm__2023-12-31__6036.csv` | `e4967ec7e0bae745c2362f306891c7c7d2eb63f3cabcfc13a6400e73acf9e2a7` | 263845 | 2026-10-14 12:07:19Z | etf (frozen-run checkpoints) | da0cf0f | no |
| `data/checkpoints/msgarch_credit/s_p_500_dry_run_development_data__ms_garch__2023-12-31__6036.csv` | `cc31f787d3b8f749066e4220f11446395df0887ddd2742767ca09d44bec211ba` | 258130 | 2026-10-14 12:10:06Z | etf (frozen-run checkpoints) | da0cf0f | no |
| `data/checkpoints/msgarch_credit/s_p_500_dry_run_development_data__ms_garch__2023-12-31__6036.params.csv` | `a64db82b2c24cb27c357c9a5e5a0f5b5c65d380eb7d0f2ee42d5f389a3c1b110` | 22814 | 2026-10-14 12:10:06Z | etf (frozen-run checkpoints) | da0cf0f | no |
| `data/es_rv_5min.csv` | `0602a1e6e44af595e4e82925ff745fc106b04ac65b917365c4ddb8a4346412fc` | 388141 | 2026-10-17 14:44:42Z | - | - | no |
| `data/fred_BAA10Y.csv` | `d68146535f8f2951a29f2854a1bd5eeac1bc67c4d92f4a471eaa9ba8dff68aed` | 168428 | 2026-10-14 11:55:54Z | etf | da0cf0f | no |
| `data/fred_DFF.csv` | `a93504210b53532fda653a7ee8d543b00b1780c83f2131e35bb94827a973c2df` | 424203 | 2026-10-17 14:44:42Z | - | - | no |
| `data/fred_GVZCLS.csv` | `4ad6cbd527c52ec9881592d4f68382831e8fdad16d69d4b313a89b9d5440538e` | 80549 | 2026-10-14 12:14:55Z | etf | da0cf0f | no |
| `data/fred_OVXCLS.csv` | `a15a52e6cc3f73f1b3dd1677f496b8eb9ce0d2f1ff795dca2d36de315c3129f5` | 85333 | 2026-10-14 12:12:16Z | etf | da0cf0f | no |
| `data/fred_RVXCLS.csv` | `35478830566fbec403c62aa349737b077b40e9054931ecf08549c7de0cd139b4` | 99968 | 2026-10-17 14:44:42Z | cross_index | 963cb5e | no |
| `data/fred_USREC.csv` | `a42a3581fe9c260dd3627febc84a7d563e5ed162cc7085a7518ebde99dc3c3b4` | 26829 | 2026-10-17 14:44:42Z | - | - | no |
| `data/fred_VIXCLS.csv` | `7f5c66eae2a2c3149c8e9762c3e8872c0fc856d487716d30ec655476b8e0b94c` | 161561 | 2026-10-14 11:57:53Z | - | - | no |
| `data/fred_VXDCLS.csv` | `f9e3939a6e4920077de198bcdee152b1eb0a8a3ba598c7eb43207f9cd52f01b9` | 127305 | 2026-10-17 14:44:42Z | cross_index | 963cb5e | no |
| `data/fred_VXEEMCLS.csv` | `c21653450ca481d45cacd0c36cba5ab98d4441091f210b50d8133e1ec09ef9dc` | 68379 | 2026-10-14 12:17:29Z | etf | da0cf0f | no |
| `data/fred_VXEWZCLS.csv` | `6977c3b5b6eda7db61f115ccfd7e31f9ef208b46a5cf94451b9294f1d19cad86` | 68389 | 2026-10-14 12:20:50Z | etf | da0cf0f | no |
| `data/fred_VXNCLS.csv` | `76f11fac54b408e8e7a86627126183f380bd852755527ebfd808c337a9398223` | 112765 | 2026-10-17 14:44:42Z | cross_index | 963cb5e | no |
| `data/macro_CFNAI_firstrelease.csv` | `d9b0504c8f602b05581cf3ea4ba12bb5446eeb66a0437c659b2ccd54099c262f` | 19512 | 2026-10-14 11:55:45Z | - | - | yes |
| `data/macro_CPILFESL_firstrelease.csv` | `e22924f4878c16240bc89b1d51318f14d625328c2fa05b3eb97e21bfdda0dd12` | 23465 | 2026-10-14 11:55:45Z | - | - | yes |
| `data/nq_rv_5min.csv` | `75ee2efd8b4860914ac5c09c18384a490bf1cfd184865c5038cf870fd686f270` | 384575 | 2026-10-17 14:44:42Z | cross_index | 963cb5e | no |
| `data/rty_rv_5min.csv` | `125e87d69132a47cccaaac13cee52d7cf938c7af912fa29e83c03a56d3e4fdf9` | 216872 | 2026-10-17 14:44:42Z | cross_index | 963cb5e | no |
| `data/ym_rv_5min.csv` | `4f59dc3f5812fd09f886f8b16e84da1c99f1059eaa6ea4d472170eec1d5cc7ed` | 388897 | 2026-10-17 14:44:42Z | cross_index | 963cb5e | no |
