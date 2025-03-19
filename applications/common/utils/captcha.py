import random, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter


class vieCode:
    __fontSize = 20  # 字体大小
    __width = 120  # 画布宽度
    __heigth = 45  # 画布高度
    __length = 4  # 验证码长度
    __draw = None  # 画布对象
    __img = None  # 图片对象
    __code = None  # 验证码字符
    __str = None  # 自定义验证码字符集
    __inCurve = True  # 是否绘制干扰曲线
    __inNoise = True  # 是否绘制干扰点
    __type = 2  # 验证码类型：1-纯字母，2-数字字母混合
    __fontPatn = 'applications/common/utils/fonts/captcha.ttf'  # 字体路径

    def GetCodeImage(self, size=80, length=4):
        """
        生成验证码图片及其对应的验证码字符。

        :param size: 验证码字体大小，默认为 80。
        :param length: 验证码字符长度，默认为 4。
        :return: 返回验证码图片对象和验证码字符。
        """
        # 准备基础数据
        self.__length = length
        self.__fontSize = size
        self.__width = self.__fontSize * self.__length
        self.__heigth = int(self.__fontSize * 1.5)

        # 生成验证码图片
        self.__createCode()
        self.__createImage()
        self.__createNoise()
        self.__printString()
        self.__cerateFilter()

        return self.__img, self.__code

    def __cerateFilter(self):
        """
        对验证码图片进行模糊处理，增加识别难度。
        """
        self.__img = self.__img.filter(ImageFilter.BLUR)
        filter = ImageFilter.ModeFilter(8)
        self.__img = self.__img.filter(filter)

    def __createCode(self):
        """
        生成验证码字符。
        """
        # 是否使用自定义字符集
        if not self.__str:
            # 源文本
            number = "3456789"
            srcLetter = "qwertyuipasdfghjkzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM"
            srcUpper = srcLetter.upper()
            if self.__type == 1:
                self.__str = number
            else:
                self.__str = srcLetter + srcUpper + number

        # 随机生成验证码字符
        self.__code = random.sample(self.__str, self.__length)

    def __createImage(self):
        """
        创建画布并设置背景颜色。
        """
        bgColor = (random.randint(200, 255), random.randint(200, 255), random.randint(200, 255))
        self.__img = Image.new('RGB', (self.__width, self.__heigth), bgColor)
        self.__draw = ImageDraw.Draw(self.__img)

    def __createNoise(self):
        """
        在验证码图片上绘制干扰点。
        """
        if not self.__inNoise:
            return
        font = ImageFont.truetype(self.__fontPatn, int(self.__fontSize / 1.5))
        for i in range(5):
            # 干扰点颜色
            noiseColor = (random.randint(150, 200), random.randint(150, 200), random.randint(150, 200))
            putStr = random.sample(self.__str, 2)
            for j in range(2):
                # 绘制干扰点
                size = (random.randint(-10, self.__width), random.randint(-10, self.__heigth))
                self.__draw.text(size, putStr[j], font=font, fill=noiseColor)

    def __createCurve(self):
        """
        在验证码图片上绘制干扰曲线。
        """
        if not self.__inCurve:
            return
        x = y = 0

        # 计算曲线系数
        a = random.uniform(1, self.__heigth / 2)
        b = random.uniform(-self.__width / 4, self.__heigth / 4)
        f = random.uniform(-self.__heigth / 4, self.__heigth / 4)
        t = random.uniform(self.__heigth, self.__width * 2)
        xend = random.randint(self.__width / 2, self.__width * 2)
        w = (2 * math.pi) / t

        # 绘制曲线
        color = (random.randint(30, 150), random.randint(30, 150), random.randint(30, 150))
        for x in range(xend):
            if w != 0:
                for k in range(int(self.__heigth / 10)):
                    y = a * math.sin(w * x + f) + b + self.__heigth / 2
                    i = int(self.__fontSize / 5)
                    while i > 0:
                        px = x + i
                        py = y + i + k
                        self.__draw.point((px, py), color)
                        i -= i

    def __printString(self):
        """
        在画布上打印验证码字符。
        """
        font = ImageFont.truetype(self.__fontPatn, self.__fontSize)
        x = 0
        # 打印字符到画布
        for i in range(self.__length):
            # 设置字体随机颜色
            color = (random.randint(30, 150), random.randint(30, 150), random.randint(30, 150))
            # 计算坐标
            x = random.uniform(self.__fontSize * i * 0.95, self.__fontSize * i * 1.1)
            y = self.__fontSize * random.uniform(0.3, 0.5)
            # 打印字符
            self.__draw.text((x, y), self.__code[i], font=font, fill=color)