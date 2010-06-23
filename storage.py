import unittest


class Storable:
    """
    class which can be stored as a text file.
    """
    def __init__(self, items=None):
        """
        Object can be created directly by passing items as dictionary.
        """
        for k,v in items.items():
            vars(self)[k] = v

    
    def getDict(self):
        """
        returns data items from this class as a dictionary.
        """
        return dict(vars(self))


def save(item, path):
    itr = item.getDict()
    d = dict(itr)
    f = open(path, "w")
    eval(str(d)) # a check to make sure everything is storable
    f.write(str(d))
    f.close()
                    

def load(path):
    f = open(path)
    data = f.read()
    return eval(data, globals(), locals())



class Test(Storable):
    
    def __init__(self, a="a",b="b", c={1:4}, items=None):
        if items:
            Storable.__init__(self, items=items)
        else:
            self.a = a
            self.b = b
            self.c = c
                
    def getDict(self):
        x = dict(vars(self))
        return x

        
class TestStorage(unittest.TestCase):
    
    def testSave(self):
        path = "/tmp/savetest"
        t = Test()
        save(t, path)
        d = load(path)
        t1 = Test(items=d)
        self.assertEqual(t.a, t1.a)
        self.assertEqual(t.b, t1.b)
        self.assertEqual(t.c, t1.c)

if __name__=="__main__":
    unittest.main()
