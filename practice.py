asin_list = []
print('Paste ASIN List\nAnd pless "f" key to finish')

while True:
    asin = input()
    if asin == 'f':
        break
    else:
        asin_list.append(asin)

print(asin_list)
