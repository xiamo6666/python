import urllib.request

if __name__ == '__main__':
    def downImg(url, folder, filename):
        urllib.request.urlretrieve(url, folder + filename)


    for a in range(50):
        downImg("https://asset1.djicdn.com/images/360/m600-pro/s1v2/1_{}.png".format(a), "/Volumes/Data/kkk/imges/",
                "{}.png".format(a))
