"""Assigment#1.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1zDOQ7DiZycLsPiQp9KkLTJIKcqIqOAjl
"""

# Commented out IPython magic to ensure Python compatibility.
import datetime, warnings, scipy 
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from sklearn import metrics, linear_model
from sklearn.metrics import r2_score
from sklearn.preprocessing import PolynomialFeatures
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from scipy.optimize import curve_fit

# %matplotlib inline
warnings.filterwarnings("ignore")

df = pd.read_csv('./flight_delay.csv', low_memory=False)
print('Dataframe dimensions:', df.shape)

def df_info(df):
  tab_info=pd.DataFrame(df.dtypes).T.rename(index={0:'column type'})
  tab_info=tab_info.append(pd.DataFrame(df.isnull().sum()).T.rename(index={0:'null values (nb)'}))
  tab_info=tab_info.append(pd.DataFrame(df.isnull().sum()/df.shape[0]*100)
                         .T.rename(index={0:'null values (%)'}))
  return tab_info

# Calculate zeros delay in whole dataset
zero_delay_whole_dataset = (df['Delay']==0).sum()
print(zero_delay_whole_dataset)
print(f"% of zero delays in dataset: {zero_delay_whole_dataset/df.shape[0]*100})")


"""**Add additional feature - Duration of the flight in minutes & Delayed Fact**"""
flight_duration = pd.to_datetime(df['Scheduled arrival time']) - pd.to_datetime(df['Scheduled depature time'])
flight_duration = pd.to_timedelta(flight_duration).astype('timedelta64[m]').astype(int)
df.info()

# Preprocessing data
df['Duration'] = flight_duration
df['Year'] = pd.DatetimeIndex(df['Scheduled depature time']).year
df['Month'] = pd.DatetimeIndex(df['Scheduled depature time']).month
df['Day'] = pd.DatetimeIndex(df['Scheduled depature time']).day
df['Scheduled depature time'] = pd.to_datetime(df['Scheduled depature time'])
df['Scheduled arrival time'] = pd.to_datetime(df['Scheduled arrival time'])
df['Depature Airport'] = df['Depature Airport'].astype("category")
df['Destination Airport'] = df['Destination Airport'].astype("category")
df['Departure time'] = df['Scheduled depature time'].dt.time
df['IS_delay'] = (df['Delay'] > 0).astype('int')


"""**Visualization**"""

"""**Missing Values**"""
#Now we will check the missing values of the dataset to detect unusable features and when and how are the rest of the missing values meaningful.
def missing_values_checker(dataframe):
  sums = dataframe.isna().sum(axis=0)
  nan_count_limit = 0
  # crate tuples (nan_sum, column_name), filter it and sort it
  non_zero_pairs = sorted([pair for pair in zip(sums, dataframe.columns) if pair[0] > nan_count_limit])
  non_zero_pairs.append((len(dataframe), 'Result'))
  # split tuples into separate lists
  non_zero_sums, non_zero_labels = zip(*non_zero_pairs)
  nans_range = np.asarray(range(len(non_zero_sums)))
  # print info
  for i, (non_zero_sum, non_zero_label) in enumerate(non_zero_pairs):
      print('{}, {}: {}'.format(i, non_zero_label, non_zero_sum))
  # plot info
  plt.figure()
  ax = plt.gca()
  ax.set_xticks(nans_range)
  plt.bar(nans_range, non_zero_sums)
  plt.show()

feature_dist = df['Depature Airport'].value_counts()
print(feature_dist)
feature_dist.count()

def check_feature_dist(feature_name,data_frame):
  carrier_count = data_frame[f"{feature_name}"].value_counts()
  sns.set(style="darkgrid")
  sns.barplot(carrier_count.index, carrier_count.values, alpha=0.9)
  plt.title(f'Frequency Distribution of {feature_name}')
  plt.ylabel('Number of Occurrences', fontsize=12)
  plt.xlabel(f'{feature_name}', fontsize=12)
  plt.show()

"""**Label encoding**"""
list_categorical_features = df.select_dtypes(include=['object']).columns.to_list()
list_categorical_features.append('Depature Airport')
list_categorical_features.append('Destination Airport')
list_categorical_features

labels_airport = df['Depature Airport']
lb_make = LabelEncoder()
integer_encoded = lb_make.fit_transform(df['Depature Airport'])
zipped = zip(integer_encoded, df['Depature Airport'])
label_airports = list(set(list(zipped)))
label_airports.sort(key = lambda x:x[0])

onehot_encoder = OneHotEncoder(sparse=False)
integer_encoded = integer_encoded.reshape(len(integer_encoded), 1)
onehot_encoded = onehot_encoder.fit_transform(integer_encoded)

correlations = df.corr()
plt.figure(figsize=(12,12))
sns.heatmap(correlations, center=0, annot=True, vmin=-1, vmax=1, cmap="BrBG")
plt.show()

# visualize the relationship between the features and the response using scatterplots
pp = sns.pairplot(df, x_vars=['Duration'], y_vars='Delay', size=7, aspect=0.7)
pp.fig.suptitle("Correlation between Duration and Delay")

# sns.pairplot(df, x_vars=['Duration'], y_vars='Delay', size=7, aspect=0.7, kind='reg')
df['DATE'] = pd.to_datetime(df[['Year','Month', 'Day']])
dep_airport = 'SVO'
df2 = df[(df['Depature Airport'] == dep_airport) & (df['Delay'] > 0)]
df2.sort_values('Scheduled depature time', inplace = True)
df2.head()

plt.figure(figsize=(12,12))
plt.scatter(df2['Scheduled depature time'], df2['Delay'], label='initial data points')
plt.title("Corelation between depart time and delay for SVO")
plt.xlabel('Departure time', fontsize = 14)
plt.ylabel('Delay', fontsize = 14)

train = df.loc[(df['Year'] <= 2017) & (df['Year'] >=2015)]
test = df.loc[df['Year'] == 2018]

# get only categorical features
cat_df_flights = train.select_dtypes(include=['object']).copy()
cat_df_flights.head()
print(cat_df_flights.columns.to_list())
print(cat_df_flights.isnull().values.sum())
print(cat_df_flights.isnull().sum())

"""**Remove outliers on delay**"""
# calculate m
mean = train['Delay'].mean()
print(mean)
# calculate standard deviation
sd = train['Delay'].std()
# determine a threhold
threshold = 2
# detect outlier
train['z_score'] = (train['Delay'] - mean)/sd

train.loc[abs(train['z_score']) > threshold, 'z_score'] = None
train = train.dropna()

pp = sns.pairplot(train, x_vars=['Duration'], y_vars='Delay', size=7, aspect=0.7)
pp.fig.suptitle("Correlation between Duration and Delay")

"""**Models execution**"""
# Apply diffrent models on dataset
from sklearn.linear_model import LinearRegression
lm = linear_model.LinearRegression()
model = lm.fit(train['Duration'].to_numpy().reshape(-1, 1), train['Delay'])
predictions = lm.predict(train['Duration'].to_numpy().reshape(-1, 1))
print("MSE_train =", metrics.mean_squared_error(predictions, train['Delay']))

lm = linear_model.LinearRegression()
model = lm.fit(train['Duration'].to_numpy().reshape(-1, 1), train['Delay'])
predictions = lm.predict(test['Duration'].to_numpy().reshape(-1, 1))
print("MSE_test =", metrics.mean_squared_error(predictions, test['Delay']))

from sklearn.metrics import accuracy_score
from sklearn.metrics import f1_score

y_pred = pd.DataFrame(data=predictions).astype('int64')
df_info(y_pred)
print(f"Accuracy score: {accuracy_score(test['Duration'], y_pred=y_pred)}")

poly = PolynomialFeatures(degree = 4)
regr = linear_model.LinearRegression()
X_ = poly.fit_transform(train['Duration'].to_numpy().reshape(-1, 1))
regr.fit(X_, train['Delay'])
result = regr.predict(X_)
print("MSE_train =", metrics.mean_squared_error(result, train['Delay']))

tips = pd.DataFrame()
tips["prediction"] = pd.Series([float(s) for s in result]) 
tips["original_data"] = pd.Series([float(s) for s in train['Delay']]) 
sns.jointplot(x="original_data", y="prediction", data=tips, size = 6, ratio = 7,
              joint_kws={'line_kws':{'color':'limegreen'}}, kind='reg')
plt.xlabel('Mean delays (min)', fontsize = 15)
plt.ylabel('Predictions (min)', fontsize = 15)
plt.plot(list(range(-10,25)), list(range(-10,25)), linestyle = ':', color = 'r')

X_ = poly.fit_transform(test['Duration'].to_numpy().reshape(-1, 1))
result = regr.predict(X_)
score = metrics.mean_squared_error(result, test['Delay'])
print("Mean squared error = ", score)

zero_delay_test_dataset = (test['Delay']==0).sum()
print(zero_delay_test_dataset)
print(f"% of zero delays in dataset: {zero_delay_test_dataset/test.shape[0]*100})")

from sklearn.linear_model import Ridge
ridgereg = Ridge(alpha=0.3,normalize=True)
poly = PolynomialFeatures(degree = 4)
X_ = poly.fit_transform(train['Duration'].to_numpy().reshape(-1, 1))
ridgereg.fit(X_, train['Delay'])

X_ = poly.fit_transform(test['Duration'].to_numpy().reshape(-1, 1))
result = ridgereg.predict(X_)
score = metrics.mean_squared_error(result, test['Delay'])
print("Mean squared error withy regurilization = ", score)
print(f"R2 score{r2_score(test['Delay'], result)}")

res_score = 10000
for rank in range(1, 4):
    for alpha in range(0, 20, 2):
        ridgereg = Ridge(alpha = alpha/10, normalize=True)
        poly = PolynomialFeatures(degree = rank)
        regr = linear_model.LinearRegression()
        X_ = poly.fit_transform(train['Duration'].to_numpy().reshape(-1, 1))
        ridgereg.fit(X_, train['Delay'])        
        X_ = poly.fit_transform(test['Duration'].to_numpy().reshape(-1, 1))
        result = ridgereg.predict(X_)
        score = metrics.mean_squared_error(result, test['Delay'])        
        if score < res_score:
            res_score = score
            parameters = [alpha/10, rank]
        print("n = {} alpha = {} , MSE = {:<0.5}".format(rank, alpha, score))

logistic_reg = LogisticRegression(penalty='l1', solver='saga')
logistic_reg.fit(train['Duration'].to_numpy().reshape(-1, 1), train['Delay'])
predictions = logistic_reg.predict(train['Duration'].to_numpy().reshape(-1, 1))
score = metrics.mean_squared_error(train['Duration'], predictions)

print("Mean squared error withy regurilization = ", score)

