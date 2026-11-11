# CropSense: Agricultural IoT & Advisory System + Machine Learning Solutions

This repository provides:
1. **Section A:** Comprehensive Step-by-Step Mathematical Solutions for all 11 Machine Learning problem statements (Image 1).
2. **Section B:** Full 5-Module Agricultural Advisory System implementation (Image 2 - DBMS, Data Engineering, ML, Full Stack, OS).

---

## Section A: Complete Mathematical Solutions to the Machine Learning Problem Statements

### Question 1: Point Classification
**Problem:** Given $w = (-1, 2)$ and $b = 1$, classify the points $x_1 = (1, 1)$ and $x_2 = (4, 1)$.
- **Decision Rule:** $g(x) = w^T x + b = w_1 x_1 + w_2 x_2 + b$
- **For $x_1 = (1, 1)$:**
  $$g(x_1) = (-1)(1) + (2)(1) + 1 = -1 + 2 + 1 = 2 > 0 \implies \mathbf{\text{Class } +1 \text{ (Positive)}}$$
- **For $x_2 = (4, 1)$:**
  $$g(x_2) = (-1)(4) + (2)(1) + 1 = -4 + 2 + 1 = -1 < 0 \implies \mathbf{\text{Class } -1 \text{ (Negative)}}$$

---

### Question 2: Perceptron Learning Algorithm
**Problem:** Use perceptron learning to find $w$ for training set $\{((-1, 1), -1), ((-2, -2), -1), ((4, 4), +1)\}$.
- Let augmented weight vector be $W = [w_1, w_2, b]^T$, initialized to $[0, 0, 0]^T$, learning rate $\eta = 1$.
- Augmented inputs: $X_1 = [-1, 1, 1]^T, y_1 = -1$; $X_2 = [-2, -2, 1]^T, y_2 = -1$; $X_3 = [4, 4, 1]^T, y_3 = +1$.
- **Epoch 1:**
  1. $X_1$: $W^T X_1 = 0 \le 0$ (Misclassified). $W \leftarrow [0, 0, 0]^T + (-1)[-1, 1, 1]^T = [1, -1, -1]^T$.
  2. $X_2$: $W^T X_2 = (1)(-2) + (-1)(-2) + (-1)(1) = -1 < 0$. Correct ($\hat{y} = -1$).
  3. $X_3$: $W^T X_3 = (1)(4) + (-1)(4) + (-1)(1) = -1 \le 0$ (Misclassified). $W \leftarrow [1, -1, -1]^T + (+1)[4, 4, 1]^T = [5, 3, 0]^T$.
- **Epoch 2:**
  1. $X_1$: $W^T X_1 = 5(-1) + 3(1) + 0 = -2 < 0$. Correct.
  2. $X_2$: $W^T X_2 = 5(-2) + 3(-2) + 0 = -16 < 0$. Correct.
  3. $X_3$: $W^T X_3 = 5(4) + 3(4) + 0 = 32 > 0$. Correct.
- **Result:** $w = (5, 3)$ with bias $b = 0$, giving decision boundary $5x_1 + 3x_2 = 0$.

---

### Question 3: Support Vector Machine Solution
**Problem:** Find the SVM solution for points: Negative class: $(2, 1), (1, 3)$; Positive class: $(6, 3)$.
- Margin constraints: $w^T x_i + b \ge 1$ for positive, $w^T x_i + b \le -1$ for negative.
- Negative points lie on line $2x_1 + x_2 = 5$. Vector to positive point $(6, 3)$ is normal to this line.
- Setting $w = (0.4, 0.2)$ and $b = -2$:
  - Negative: $0.4(2) + 0.2(1) - 2 = -1.0$ (Support Vector)
  - Negative: $0.4(1) + 0.2(3) - 2 = -1.0$ (Support Vector)
  - Positive: $0.4(6) + 0.2(3) - 2 = +1.0$ (Support Vector)
- **Optimal Hyperplane:** $0.4 x_1 + 0.2 x_2 - 2 = 0 \iff 2x_1 + x_2 - 10 = 0$.
- **Weights:** $w = \left(\frac{2}{5}, \frac{1}{5}\right)$, $b = -2$. Margin width $= \frac{2}{\|w\|} = 2\sqrt{5} \approx 4.472$.

---

### Question 4: XOR Non-Linearity Proof & Solution
**Problem:** Show XOR cannot be solved by a linear function in $x_1, x_2$, but can be solved using $x_1 x_2$.
- **Proof:** XOR table: $(0,0)\to 0, (0,1)\to 1, (1,0)\to 1, (1,1)\to 0$.
  If linear $w_1 x_1 + w_2 x_2 + w_0$ exists:
  $w_0 < 0$
  $w_1 + w_0 > 0$
  $w_2 + w_0 > 0$
  $w_1 + w_2 + w_0 < 0$
  Summing positive inequalities gives $(w_1 + w_2 + w_0) + w_0 > 0$, but LHS is sum of two negative numbers, yielding a contradiction.
- **Solution using $x_1 x_2$:**
  With feature mapping $\phi(x) = [x_1, x_2, x_1 x_2]^T$, discriminant:
  $$g(x) = x_1 + x_2 - 2x_1 x_2 - 0.5$$
  - $(0,0): -0.5 < 0 \implies 0$
  - $(0,1): +0.5 > 0 \implies 1$
  - $(1,0): +0.5 > 0 \implies 1$
  - $(1,1): 1 + 1 - 2 - 0.5 = -0.5 < 0 \implies 0$

---

### Question 5: Logistic Regression Discriminant Function
**Problem:** Apply logistic regression to data: $x_1=(1,2), x_2=(2,1), x_3=(6,7), x_4=(7,6)$ with $y_1=0, y_2=0, y_3=1, y_4=1$.
- Class 0 centroid: $\mu_0 = (1.5, 1.5)$; Class 1 centroid: $\mu_1 = (6.5, 6.5)$.
- The separating direction is along $(1, 1)$, midpoint is $(4, 4)$.
- **Discriminant Function (Log-odds):** $g(x) = w(x_1 + x_2 - 8)$.
- **Decision Boundary ($P=0.5$):** $x_1 + x_2 - 8 = 0$.
- **Posterior Probability:** $P(Y=1|x) = \sigma(w(x_1 + x_2 - 8)) = \frac{1}{1 + e^{-w(x_1 + x_2 - 8)}}$.

---

### Question 6: Distance of Point from Decision Boundary
**Problem:** Find the distance of point $x=(3, 4)$ from decision boundary $2x_1 + 3x_2 - 6 = 0$.
- Perpendicular distance formula:
  $$d = \frac{|a x_0 + b y_0 + c|}{\sqrt{a^2 + b^2}} = \frac{|2(3) + 3(4) - 6|}{\sqrt{2^2 + 3^2}} = \frac{|6 + 12 - 6|}{\sqrt{13}} = \frac{12}{\sqrt{13}} \approx 3.3282$$

---

### Question 7: Soft-Margin SVM Lagrangian & KKT Conditions
**Problem:** For soft-margin SVM, write the Lagrangian and derive the KKT conditions.
- **Primal Problem:** $\min_{w, b, \xi} \frac{1}{2}\|w\|^2 + C\sum_{i=1}^n \xi_i$ subject to $y_i(w^T x_i + b) \ge 1 - \xi_i$ and $\xi_i \ge 0$.
- **Lagrangian:**
  $$\mathcal{L}(w, b, \xi, \alpha, \mu) = \frac{1}{2}\|w\|^2 + C\sum_{i=1}^n \xi_i - \sum_{i=1}^n \alpha_i [y_i(w^T x_i + b) - 1 + \xi_i] - \sum_{i=1}^n \mu_i \xi_i$$
- **KKT Conditions:**
  1. $\nabla_w \mathcal{L} = w - \sum_{i=1}^n \alpha_i y_i x_i = 0 \implies w = \sum_{i=1}^n \alpha_i y_i x_i$
  2. $\frac{\partial \mathcal{L}}{\partial b} = -\sum_{i=1}^n \alpha_i y_i = 0 \implies \sum_{i=1}^n \alpha_i y_i = 0$
  3. $\frac{\partial \mathcal{L}}{\partial \xi_i} = C - \alpha_i - \mu_i = 0 \implies \alpha_i + \mu_i = C$
  4. Primal Feasibility: $y_i(w^T x_i + b) \ge 1 - \xi_i, \; \xi_i \ge 0$
  5. Dual Feasibility: $\alpha_i \ge 0, \; \mu_i \ge 0 \implies 0 \le \alpha_i \le C$
  6. Complementary Slackness: $\alpha_i [y_i(w^T x_i + b) - 1 + \xi_i] = 0$ and $(C - \alpha_i)\xi_i = 0$.

---

### Question 8: Polynomial Kernel Feature Mapping
**Problem:** Given kernel $K(x_i, x) = (1 + x_i^T x)^2$, find the feature mapping for 2D input.
- For $x = (x_1, x_2)^T$ and $z = (z_1, z_2)^T$:
  $K(z, x) = (1 + z_1 x_1 + z_2 x_2)^2 = 1 + 2z_1 x_1 + 2z_2 x_2 + z_1^2 x_1^2 + 2z_1 z_2 x_1 x_2 + z_2^2 x_2^2$.
- Matching $\phi(z)^T \phi(x)$:
  $$\mathbf{\phi(x) = \left[ 1, \; \sqrt{2}x_1, \; \sqrt{2}x_2, \; x_1^2, \; \sqrt{2}x_1 x_2, \; x_2^2 \right]^T \in \mathbb{R}^6}$$

---

### Question 9: Boolean OR Linear Discriminant Function
**Problem:** For Boolean OR function, find a linear discriminant function that separates classes.
- Inputs $(0,0)\to 0$, others $\to 1$.
- **Discriminant Function:** $g(x) = x_1 + x_2 - 0.5$
  - $g(0,0) = -0.5 < 0 \implies 0$
  - $g(0,1) = 0.5 > 0 \implies 1$
  - $g(1,0) = 0.5 > 0 \implies 1$
  - $g(1,1) = 1.5 > 0 \implies 1$

---

### Question 10: Boolean AND Linear Discriminant Function
**Problem:** For Boolean AND function, find a linear discriminant function that separates classes.
- Inputs $(1,1)\to 1$, others $\to 0$.
- **Discriminant Function:** $g(x) = x_1 + x_2 - 1.5$
  - $g(0,0) = -1.5 < 0 \implies 0$
  - $g(0,1) = -0.5 < 0 \implies 0$
  - $g(1,0) = -0.5 < 0 \implies 0$
  - $g(1,1) = 0.5 > 0 \implies 1$

---

### Question 11: SVM Margin Computation
**Problem:** Compute the margin for SVM with $w=(1, 2)$ and $b=-3$.
- $\|w\| = \sqrt{1^2 + 2^2} = \sqrt{5}$.
- **Total Margin Corridor Width:**
  $$\mathbf{M = \frac{2}{\|w\|} = \frac{2}{\sqrt{5}} = \frac{2\sqrt{5}}{5} \approx 0.8944}$$
- **Geometric Half-Margin:** $\gamma = \frac{1}{\|w\|} = \frac{1}{\sqrt{5}} \approx 0.4472$.
- Note: The intercept $b=-3$ shifts the hyperplane position but does not alter the margin width.

---

## Section B: CropSense 5-Module Agricultural System Architecture

```
Assignment-Prob/
├── dbms_module/               # 1. DBMS: Schema, relational entities, DDL
├── data_engineering_module/   # 2. Data Eng: ETL pipeline, cleaning, anomalies
├── ml_module/                 # 3. ML: Yield regression + Drought/Pest classification
├── fullstack_module/          # 4. Full Stack: Web dashboard (Vercel/Render ready)
├── os_module/                 # 5. OS: Multi-threaded sensor daemon & buffer
└── tests/                     # Integration test suite
```

### Running the System
```bash
# Run unit & integration tests
python tests/test_all_modules.py

# Launch Full Stack Web Dashboard & API
python run_server.py
```
Open `http://127.0.0.1:5000` in your web browser.

---

### Managing and Deleting Database Records

#### 1. Via Dashboard UI (Easiest)
- **Delete Single Row:** Click the **`🗑️ Delete`** button on any record in the *Stored Telemetry & Advisory Records* table.
- **Clear All Logs:** Click the **`🗑️ Clear All`** button in the header of the table to wipe all historical telemetry and advisories.

#### 2. Via Python
```python
from dbms_module.db_manager import delete_sensor_reading, clear_all_telemetry

# Delete a single record by ID:
delete_sensor_reading(17)

# Or delete all stored telemetry readings & advisories:
clear_all_telemetry()
```

#### 3. Via SQLite CLI
```bash
sqlite3 dbms_module/cropsense_master.db "DELETE FROM sensor_readings WHERE reading_id = 17;"
sqlite3 dbms_module/cropsense_master.db "DELETE FROM sensor_readings; DELETE FROM advisories;"
```
