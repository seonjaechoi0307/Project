# Kamp-AI 인공지능 공모전

## 프로젝트 데이터 셋 : 열처리 뿌리금형

### 문제 정의
- 숙련공에 의존하는 작업 환경으로 작업자별 숙련도에 따른 생산 품질 변동
- 열처리 설비 공정 진행 시 육안으로는 확인하기 어렵다는 점
- 작업자의 문제인지 설비의 문제인지 정확히 알 수 없었다는 점

### 분석 기대효과
- 숙련도 의존 공정에서 데이터 기반 스마트 팩토리로 변동됨에 따른 품질 신뢰도 증가
- 고품질의 제품 제조가 수월해짐에 따른 손해 비용 최소화
- 설비의 이상 주기를 예측하여 예지보전을 통한 미래 손해 방지

- - -
## Use Pingouin Library 통계 분석

> Import Pingouin
```
import pingouin as pg

columns = df_104126.columns.tolist()
columns.remove('DZ1_OP')
```

> columns Output
```
['DZ2_OP',
 'DZ1_TEMP',
 'DZ2_TEMP',
 'CLEAN',
 'HDZ1_OP',
 'HDZ2_OP',
 'HDZ3_OP',
 'HDZ4_OP',
 'HDZ_CP',
 'HDZ_CPM',
 'HDZ1_TEMP',
 'HDZ2_TEMP',
 'HDZ3_TEMP',
 'HDZ4_TEMP',
 'SCZ1_TEMP',
 'SCZ2_TEMP',
 'STZ1_TEMP',
 'STZ2_TEMP']
```

> T-Test Code
```
statistic_1 = pg.ttest(df_104126['DZ1_OP'], df_128795['DZ1_OP'])
statistic_1.insert(0, 'Machine', 'DZ1_OP')

statistic_list = [statistic_1]

for column in columns:
    statistic_2 = pg.ttest(df_104126[column], df_128795[column])
    statistic_2.insert(0, 'Machine', column)
    statistic_list.append(statistic_2)

statistic_3 = pd.concat(statistic_list, ignore_index=True)
```
- - -
### T-Test 테이블
```
통계지표 개념정리

1. T: t-검정 통계량입니다. 이 값은 두 그룹 간 평균의 차이가 표준오차로 나눈 값입니다.
절대값이 크면 클수록, 두 그룹 간의 차이가 더 유의미하다는 것을 의미합니다.

2. dof (Degrees of Freedom): 자유도를 나타냅니다.
이는 표본 크기와 변수의 개수에 따라 결정됩니다.

3. alternative: 검정이 양측 검정(two-sided)인지를 나타냅니다.
이는 두 그룹 간의 차이가 양의 방향이든 음의 방향이든 상관없이 차이가 있는지를 검정합니다.

4. p-val (P-Value): 귀무가설 하에서 관측된 결과가 나타날 확률입니다.
일반적으로 p-value가 0.05 또는 0.01 이하일 때, 결과를 통계적으로 유의미하다고 판단합니다.

5. CI95% (95% Confidence Interval): 평균 차이의 95% 신뢰 구간입니다.
이 구간이 0을 포함하지 않으면, 평균 차이가 통계적으로 유의미하다고 할 수 있습니다.

6. cohen-d: 효과 크기(effect size)를 나타내는 지표로,
두 그룹 간의 차이가 얼마나 의미 있는지를 나타냅니다. 값이 클수록 효과 크기가 크다는 것을 의미합니다.

7. BF10: 베이지안 팩터로, 귀무가설 대비 대립가설의 지지 정도를 나타냅니다.
일반적으로 이 값이 3 이상이면 대립가설을 지지한다고 해석합니다.

8. power: 검정의 통계적 검정력을 나타냅니다.
1에 가까울수록 높은 검정력을 가지며, 일반적으로 0.8 이상이면 적절한 검정력을 가진 것으로 간주합니다.

해석:

1. 모든 변수에서 p-value가 매우 낮거나 0입니다.
이는 두 데이터셋 간에 각 변수에 대해 통계적으로 유의미한 차이가 있다는 것을 의미합니다.

2. 'T' 값이 양수인 경우 df_104126의 평균이 df_128795보다 높았음을, 음수인 경우는 반대임을 나타냅니다.

3. Cohen-d 값은 효과 크기를 나타내며, 값이 클수록 두 그룹 간의 차이가 더 크다는 것을 의미합니다.
예를 들어, 'CLEAN' 변수에서의 Cohen-d 값은 9.791977로, 매우 큰 효과 크기를 나타냅니다.

4. 검정력(power)이 대부분의 경우 1에 가까우므로, 이 검정들은 높은 검정력을 가진다고 할 수 있습니다.
```

![T-Test 지표](./image/Statistic_Table.png)
- - -