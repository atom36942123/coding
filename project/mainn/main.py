print("main started")

def func():
    print("function called")

print("main if before")
if __name__ == '__main__':
    func()
else:
    print("else called")
    
print("main if after")