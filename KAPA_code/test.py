#!/usr/bin/env python3
"""
Test Script: a test script
Date: 10/05/2020
Author: Emily Ramey
"""

class Test1:
    """
    A test class.
    
    Attributes:
    
        a: int
        b: int
    
    """
    
    def __init__(self, a=0, b=0):
        """
        Initializer for class Test1
        
        Parameters:
            
            a (int): an int
            b (int): another int
            
        """
        self.a = a
        self.b = b
    
    def testfunc(self):
        """ Returns a+b """
        return self.a+self.b