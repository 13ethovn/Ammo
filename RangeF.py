<<<<<<< HEAD
import numpy as np
import matplotlib.pyplot as plt

# 生成x值，从-2π到2π，总共1000个点
x = np.linspace(200, 1200, 1000)

# 计算y值
y = np.sin(x)

# range = 20 speed f 1−(1−f) life∗20

# 创建图像
plt.figure(figsize=(8, 6))

# 绘制曲线
plt.plot(x, y)

# 添加标题和标签
plt.title('Graph of  $ y = \sin(x) $ ')
plt.xlabel('x')
plt.ylabel('y')

# 显示网格
plt.grid(True)

# 显示图像
=======
import numpy as np
import matplotlib.pyplot as plt

# 生成x值，从-2π到2π，总共1000个点
x = np.linspace(200, 1200, 1000)

# 计算y值
y = np.sin(x)

# range = 20 speed f 1−(1−f) life∗20

# 创建图像
plt.figure(figsize=(8, 6))

# 绘制曲线
plt.plot(x, y)

# 添加标题和标签
plt.title('Graph of  $ y = \sin(x) $ ')
plt.xlabel('x')
plt.ylabel('y')

# 显示网格
plt.grid(True)

# 显示图像
>>>>>>> origin/main
plt.show()