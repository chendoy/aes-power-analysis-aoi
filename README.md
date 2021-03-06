# When Algorithm Meets Reality

## Correlation Power Analysis

This code demonstrates power analysis attack on the server at http://aoi.ise.bgu.ac.il/ as part of the class "Attacks on Implementations of Secure Systems" by Dr. Yossi Oren @BGU, spring 2021. A simulated AES implementation is running on this server and the secret key needs to be revealed.

### Getting Traces

http://aoi.ise.bgu.ac.il/encrypt?user=chendoy&difficulty=1

The server responds with a JSON string with two fields: "plaintext" and "leaks". The mission is to reveal the secret AES key by using Correlation Power Analysis (CPA). Every username is valid.

### Verifying a Key

A guessed key can be verified using this address, which returns 1 if the key is correct:

http://aoi.ise.bgu.ac.il/verify?user=chendoy&difficulty=2&key=d60aff3115a72dfc887aa468e2fd2f5c

### How to Run?
```python3 ex02_M2.py [filename]```

For example: ```python3 ex02_M2.py traces```