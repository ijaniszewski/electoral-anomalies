# Electoral Anomalies

This repository contains code, data, and analysis for detecting localized electoral anomalies in Polish elections using robust spatial statistical methods. Inspired by the 2025 presidential runoff study by Kontek & Merope, we investigate whether similar patterns of statistical outliers in vote shares, turnout, and ballot usage occur systematically across multiple election cycles in Poland.

We begin with the 2025 presidential election and will progressively extend the analysis to earlier elections. Our working hypothesis is that statistical anomalies—defined relative to geographically local voting norms—are not isolated incidents but recurring features of the electoral landscape.

The methodology is based on localized clustering of polling stations by postal code proximity and the application of Median Absolute Deviation (MAD) thresholds across multiple voting metrics. The goal is to provide a transparent, reproducible, and scalable framework for anomaly detection and electoral integrity auditing.