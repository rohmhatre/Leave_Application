import pandas as pd

pd.DataFrame({'NAME':['syed shabaaz'],'Roll Number':['25m0005']}).to_excel('students.xlsx',index=False)
print('created')
