import matplotlib.pyplot as plt
import seaborn as sns

xs = [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]
ys = [1, 2, 4, 13, 12, 16, 16, 16, 16 ,16]

sns.lineplot(x=xs,y=ys)
plt.xlabel('Number of Traces')
plt.ylabel('Number of Correct Bytes')
plt.title('Correct Bytes Count as a function of # of Traces')
plt.savefig('fig')