## How to run the script to process each year on EDU cluster server

To process the data concurrent on EDU cluster server we will split PDF files into 280 directories.
Please note we have quota for 300 CPU cores and 1TB memory limit so we will submit only 280 jobs with 1 CPU core and 3.5G of RAM each.


1) For each year follow the steps in the `notebooks` to prepare and setup the stuffs to process PDF files on cluster server

2) Submit job to process on cluster server

```
qsub kerala_2016.qsub
```

3) Check the status of running job

```
showq
```
