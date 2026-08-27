# SEC Open Data API — endpoint index

_Generated from `spec/developer-full.json`._

## 69c13faefc6de60d56bb7735 (6)

| Method | Path | Operation id |
|---|---|---|
| GET | `/v2/bond/issuers` | 68cbc1d76d589587c9d523b2 |
| GET | `/v2/bond/features` | getBondFeatures |
| GET | `/v2/bond/credit-ratings` | bond-credit-rating |
| GET | `/v2/bond/outstanding-values` | 68cbc0feccdd66fa18db1b66 |
| GET | `/v2/bond/involve-parties` | 68cbc150948d12521d4c842e |
| GET | `/v2/bond/investor-holdings` | 68cbc18e81f0eb3cde73e187 |

## digital-asset (1)

| Method | Path | Operation id |
|---|---|---|
| POST | `/v1/digital-asset/profile/intermediary` | 01-profile-intermediary |

## fund (21)

| Method | Path | Operation id |
|---|---|---|
| GET | `/v2/fund/general-info/amcs` | getAmcList |
| GET | `/v2/fund/general-info/profiles` | getFundProfile |
| GET | `/v2/fund/general-info/specifications` | getFundSpecification |
| GET | `/v2/fund/general-info/mutual-fund-fees` | getMutualfundFee |
| GET | `/v2/fund/general-info/involve-parties` | getFundRelative |
| GET | `/v2/fund/factsheet/urls` | getFactsheetUrl |
| GET | `/v2/fund/factsheet/ipos` | getFactsheetIPO |
| GET | `/v2/fund/factsheet/benchmarks` | getFactsheetBenchmark |
| GET | `/v2/fund/factsheet/subscription-redemption-minimums` | getFactsheetRedemptionInvestment |
| GET | `/v2/fund/factsheet/subscription-redemption-periods` | getFactsheetRedemption |
| GET | `/v2/fund/factsheet/risk-spectrum` | getFactsheetRiskSpectrum |
| GET | `/v2/fund/factsheet/statistics` | getFactsheetStatisticsinfo |
| GET | `/v2/fund/factsheet/dividend-policy` | getFactsheetDividend |
| GET | `/v2/fund/factsheet/fees` | getFactsheetFee |
| GET | `/v2/fund/factsheet/performance` | getFactsheetPerformance |
| GET | `/v2/fund/factsheet/asset-allocation` | getFactsheetAssetAllocation |
| GET | `/v2/fund/factsheet/top5-holdings` | getFactsheetTop5Holding |
| GET | `/v2/fund/outstanding/portfolio` | get-outstanding-port |
| GET | `/v2/fund/outstanding/portfolio-asset-type` | get-outstanding-portassettype |
| GET | `/v2/fund/daily-info/nav` | getFundDailyInfoNAV |
| GET | `/v2/fund/daily-info/dividend-history` | getFundDailyInfoDividendHistory |

## license-check (15)

| Method | Path | Operation id |
|---|---|---|
| POST | `/v1/license-check/licensee/person` | 01-ค้นหาบุคคลที่ได้รับความเห็นชอบจากสำนักงานด้วยส่วนหนึ่งของชื่อหรือเลขทะเบี |
| GET | `/v1/license-check/licensee/company` | 02-นิติบุคคลที่เคยได้รับใบอนุญาตจากสำนักงาน-หรือเคยจดทะเบียนประกอบธุรกิจกับส |
| POST | `/v1/license-check/licensee/company` | 03-นิติบุคคลที่ได้รับความเห็นชอบจากสำนักงานด้วยส่วนหนึ่งของชื่อ |
| GET | `/v1/license-check/licensee/person/{unique_id}/license` | 04-ประเภทความเห็นชอบของบุคคลที่ได้รับความเห็นชอบจากสำนักงาน |
| GET | `/v1/license-check/licensee/company/{unique_id}/personnel` | 05-การปฏิบัติหน้าที่ของบุคคลภายใต้นิติบุคคล |
| GET | `/v1/license-check/licensee/person/{unique_id}/work_info` | 06-การปฎิบัติหน้าที่บุคคลที่ได้รับความเห็นชอบจากสำนักงาน |
| GET | `/v1/license-check/licensee/company/{unique_id}/license` | 07-ประเภทใบอนุญาต-การจดทะเบียนของนิติบุคคลที่ได้รับใบอนุญาตจากสำนักงาน |
| GET | `/v1/license-check/licensee/company/{unique_id}/business_act` | 08-การประกอบธุรกิจในปัจจุบันของนิติบุคคลที่ได้รับใบอนุญาตจากสำนักงาน |
| GET | `/v1/license-check/licensee/{unique_id}/enforcement` | 09-ประเภทความผิดและการกระทำของบุคคล-นิติบุคคลที่ได้รับความเห็นชอบ-ใบอนุญาตขอ |
| GET | `/v1/license-check/licensee/{unique_id}/enforcement/{case_id}` | 10-การดำเนินการกับความผิดของบุคคล-นิติบุคคลที่ได้รับความเห็นชอบ-ใบอนุญาตของส |
| GET | `/v1/license-check/licensee/investoralert/alertdetail` | 5d2bd07a4f173fb37a906d84 |
| GET | `/v1/license-check/licensee/investoralert/{case_id}/alertaction` | 5d2bd07a4f173fb37a906d83 |
| GET | `/v1/license-check/licensee/auditors` | 5d2bd07a4f173fb37a906d85 |
| GET | `/v1/license-check/licensee/auditingFirm` | 5d2bd07a4f173fb37a906d86 |
| GET | `/v1/license-check/licensee/auditors/search/name/{person_name}` | get-licensee-auditors-search-name-person_name |

## one-report (23)

| Method | Path | Operation id |
|---|---|---|
| GET | `/v1/one-report/sbo/{report_year}/info/{language}` | 01-SBO-Info |
| GET | `/v1/one-report/sbo/{report_year}/rd/{unique_id}` | 02-SBO-RD |
| GET | `/v1/one-report/sbo/{report_year}/product_income/{unique_id}` | 03-SBO-Product-Income |
| GET | `/v1/one-report/sbo/{report_year}/export_income/{unique_id}` | 04-SBO-Export-Income |
| GET | `/v1/one-report/sbo/{report_year}/risk/{unique_id}` | 05-SBO-Risk-Detail |
| GET | `/v1/one-report/sustainability/{report_year}/detail/{unique_id}` | 06-Sustainability-Detail |
| GET | `/v1/one-report/sustainability/{report_year}/environment_issue/{unique_id}` | 07-Sustainability-Environment_issue |
| GET | `/v1/one-report/sustainability/{report_year}/humanrights_issue/{unique_id}` | 08-Sustainability-Humanrights_issue |
| GET | `/v1/one-report/scp/{report_year}/employee_info/{unique_id}` | 09-SocialPerformance-Employee_info |
| GET | `/v1/one-report/scp/{report_year}/employee_development/{unique_id}` | 10-SocialPerformance-Employee_development |
| GET | `/v1/one-report/scp/{report_year}/labor_dispute/{unique_id}` | 11-SocialPerformance-Labor_dispute |
| GET | `/v1/one-report/scp/{report_year}/csr_activity/{unique_id}` | 12-SocialPerformance-CSR_Activity |
| GET | `/v1/one-report/cgp/{report_year}/governance/{unique_id}` | 13-CGP-Governance |
| GET | `/v1/one-report/cgp/{report_year}/director/{unique_id}` | 14-CGP-Director |
| GET | `/v1/one-report/cgp/{report_year}/code_of_conduct/{unique_id}` | 15-CGP-CodeofConduct |
| GET | `/v1/one-report/fs/{report_year}/financial_statement/{unique_id}` | 16-CGP-FinancialStatement |
| GET | `/v1/one-report/cgs/{report_year}/board/{unique_id}` | 17-CGS-Board |
| GET | `/v1/one-report/cgs/{report_year}/employee/{unique_id}` | 18-CGS-Employee |
| GET | `/v1/one-report/cgs/{report_year}/auditor_company/{unique_id}` | 19-CGS-AuditorCompany |
| GET | `/v1/one-report/cgs/{report_year}/director_performance/{unique_id}` | 20-CGS-DirectorPerformance |
| GET | `/v1/one-report/cgs/{report_year}/bods/{unique_id}` | 21-CGS-Bods |
| GET | `/v1/one-report/cgs/{report_year}/executives/{unique_id}` | 22-CGS-Executives |
| GET | `/v1/one-report/cgs/{report_year}/committees/{unique_id}/others` | 23-CGS-Committees-Others |

## pvd (15)

| Method | Path | Operation id |
|---|---|---|
| GET | `/v1/pvd/factsheet/amc` | 01-Factsheet-Amc |
| GET | `/v1/pvd/factsheet/{unique_id}/fund` | 02-Factsheet-Fund |
| POST | `/v1/pvd/factsheet/fund` | 03-Factsheet-Fund |
| GET | `/v1/pvd/factsheet/{proj_id}/policy` | 04-Factsheet-Policy |
| GET | `/v1/pvd/factsheet/{proj_id}/return` | 05-PVD-Factsheet-Return |
| GET | `/v1/pvd/factsheet/{proj_id}/trailreturn` | 06-PVD-Factsheet-returntrail |
| GET | `/v1/pvd/factsheet/{proj_id}/fee` | 07-PVD-Factsheet-Fee |
| GET | `/v1/pvd/factsheet/{proj_id}/PVDFullPort/{period}` | 08-PVD-Factsheet-FullPortPvd |
| GET | `/v1/pvd/factsheet/{proj_id}/statistics` | 09-PVD-Factsheet-statistics |
| GET | `/v1/pvd/factsheet/{proj_id}/top5/assettype` | 10-PVD-Factsheet-top5-assettype |
| GET | `/v1/pvd/factsheet/{proj_id}/top5/securities` | 11-PVD-Factsheet-top5-securities |
| GET | `/v1/pvd/factsheet/{proj_id}/top5/foreign` | 12-PVD-Factsheet-top5-foreign |
| GET | `/v1/pvd/factsheet/{proj_id}/top5/industry` | 13-PVD-Factsheet-top5-industry |
| GET | `/v1/pvd/factsheet/{proj_id}/top5/issuer` | 14-PVD-Factsheet-top5-issuer |
| GET | `/v1/pvd/factsheet/{proj_id}/nav/{nav_date}` | 15-PVD-Factsheet-nav |

