#!/usr/bin/env python
# coding: utf-8

# In[2]:


import numpy as np
import pandas as pd
from astropy.table import Table
import ML_util
from sklearn.svm import SVR
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_absolute_error


# In[3]:


meta_clean = ML_util.read_and_clean()
meta_clean.head()


# In[4]:


X = meta_clean[ML_util.use_cols[2:]]
strehl = meta_clean[ML_util.use_cols[0]]
fwhm = meta_clean[ML_util.use_cols[1]]


# In[5]:


y = strehl
train_X, test_X, train_y, test_y = train_test_split(X, y)


# In[13]:


svm = SVR(kernel='poly', degree=7, C=0.1, gamma='scale')
svm.fit(train_X, train_y)

train_pred = svm.predict(train_X)
test_pred = svm.predict(test_X)

train_err = mean_absolute_error(train_pred, train_y)
test_err = mean_absolute_error(test_pred, test_y)

print("Training error:", train_err, "\nTesting error:", test_err)


# In[ ]:


params = {'kernel': ['poly'], 'degree':range(1, 10), 
          'coef0':[1], 'C':[x for x in np.arange(0.1,5,0.1)], 'gamma':['scale']}

svm = SVR()
search = GridSearchCV(svm, params, cv=5, scoring="neg_mean_absolute_error")
search.fit(train_X, train_y)

train_pred = search.predict(train_X)
test_pred = search.predict(test_X)

train_err = mean_absolute_error(train_pred, train_y)
test_err = mean_absolute_error(test_pred, test_y)

print("Training error:", train_err, "\nTesting error:", test_err)


# In[ ]:


best = search.best_estimator_
params = search.best_params_
print(params)


