## Unit 1 — System of Linear Equations

Unit 1 syllabus includes: **rank of matrix, echelon form, homogeneous/non-homogeneous systems, consistency/inconsistency, Gauss elimination, inverse of matrix, and Gauss-Jordan method**. 
From past papers, this unit is **high scoring and repeated every year**: rank/echelon, consistency, Gauss elimination, Gauss-Jordan inverse, and homogeneous systems with trivial/non-trivial solutions appear again and again.    

---

# Concept summary

A **system of linear equations** means equations like:

[
a_1x+b_1y+c_1z=d_1
]

We usually write it as:

[
AX=B
]

where:

[
A=\text{coefficient matrix},\quad X=\text{variables},\quad B=\text{constants}
]

Example:

[
x+2y-z=3
]

Here coefficients are (1,2,-1), variables are (x,y,z), and constant is (3).

---

## Priority list from previous papers

| Topic                                            |                      Priority | Why                                         |
| ------------------------------------------------ | ----------------------------: | ------------------------------------------- |
| Rank of matrix by echelon form                   |            **Very Important** | Asked repeatedly in Section-A and Section-B |
| Gauss elimination method                         |            **Very Important** | Direct solving question appears often       |
| Homogeneous system: trivial/non-trivial solution |            **Very Important** | Repeated with determinant/rank condition    |
| Consistency and inconsistency                    |            **Very Important** | Asked as short + long type                  |
| Gauss-Jordan method for inverse                  |            **Very Important** | Direct inverse questions repeated           |
| Solving system using inverse matrix              |                 **Important** | Asked in 2024 paper                         |
| Column rank / row rank                           |                 **Important** | Asked in short questions                    |
| Definition/state Gauss-Jordan method             |                 **Important** | Appears as theory short note                |
| Large 4×4 inverse                                | **Low Priority but possible** | Appeared once, lengthy but method same      |

---

# Important formulas

## 1. Rank of a matrix

The **rank** of a matrix is the number of **non-zero rows** in its echelon form.

Example:

[
\begin{bmatrix}
1&2&3\
0&1&4\
0&0&0
\end{bmatrix}
]

Number of non-zero rows = 2

[
\therefore \text{Rank}=2
]

---

## 2. Echelon form rules

A matrix is in echelon form if:

1. All zero rows are at the bottom.
2. First non-zero element of each row is to the right of the row above.
3. Elements below leading entries are zero.

---

## 3. Consistency condition

For a non-homogeneous system:

[
AX=B
]

Compare:

[
\rho(A) \quad \text{and} \quad \rho([A:B])
]

where (\rho) means rank.

### Cases

| Condition                 | Result                     |
| ------------------------- | -------------------------- |
| (\rho(A)\neq \rho([A:B])) | No solution / inconsistent |
| (\rho(A)=\rho([A:B])=n)   | Unique solution            |
| (\rho(A)=\rho([A:B])<n)   | Infinite solutions         |

Here (n) = number of unknowns.

---

## 4. Homogeneous system

A homogeneous system has RHS zero:

[
AX=0
]

Example:

[
x+2y-z=0
]

A homogeneous system is **always consistent** because:

[
x=0,\ y=0,\ z=0
]

is always a solution.

### For square matrix

[
AX=0
]

| Condition | Result |         |                             |
| --------- | ------ | ------- | --------------------------- |
| (         | A      | \neq 0) | Only trivial solution       |
| (         | A      | =0)     | Non-trivial solution exists |

---

## 5. Inverse method

For:

[
AX=B
]

If (A^{-1}) exists, then:

[
X=A^{-1}B
]

Use only when matrix is square and determinant is non-zero.

---

## 6. Gauss elimination method

Main idea:

Convert system into **upper triangular form**, then use back substitution.

Example form:

[
\begin{aligned}
x+2y+z&=5\
3y-z&=4\
2z&=6
\end{aligned}
]

First find (z), then (y), then (x).

---

## 7. Gauss-Jordan method

Main idea:

Convert:

[
[A:I]\to[I:A^{-1}]
]

So, for inverse:

[
[A:I]
]

Apply row operations until left side becomes identity matrix.

Then right side becomes:

[
A^{-1}
]

---

# Repeated question patterns from past papers

## Pattern 1: Find rank using echelon form — **Very Important**

Common wording:

> Using echelon form, find the rank of the matrix.

This appeared in multiple papers as direct rank/echelon questions.    

---

## Pattern 2: Solve system by Gauss elimination — **Very Important**

Common wording:

> Solve the system using Gauss elimination method.

This appears as a long-answer problem.  

---

## Pattern 3: Find inverse using Gauss-Jordan — **Very Important**

Common wording:

> Find the inverse of the matrix using Gauss-Jordan method.

This appears repeatedly in Section-B.  

---

## Pattern 4: Homogeneous system and value of parameter — **Very Important**

Common wording:

> Determine the value of (k) for which the homogeneous system has only trivial solution / non-trivial solution.

This appeared repeatedly.   

---

## Pattern 5: Consistency of system — **Very Important**

Common wording:

> Determine whether the system is consistent or inconsistent.

This appeared in short-answer form. 

---

# Most probable questions

1. **Find rank of a matrix by reducing it to echelon form.**
2. **Solve a system of 3 linear equations using Gauss elimination.**
3. **Find inverse of a 3×3 matrix using Gauss-Jordan method.**
4. **Determine whether a given system is consistent or inconsistent.**
5. **Find values of (k) for which a homogeneous system has trivial/non-trivial solution.**
6. **Solve system using inverse matrix method.**
7. **State Gauss-Jordan method.**
8. **Explain rank of matrix / column rank.**

---

# Solved Example 1 — Rank by echelon form

Find the rank of:

[
A=
\begin{bmatrix}
3&1&7\
1&2&4\
4&-1&7\
4&-1&5
\end{bmatrix}
]

## Step 1: Interchange rows for easy calculation

Take row 2 as row 1:

[
R_1=[1,2,4]
]

Matrix becomes:

[
\begin{bmatrix}
1&2&4\
3&1&7\
4&-1&7\
4&-1&5
\end{bmatrix}
]

## Step 2: Make entries below first pivot zero

[
R_2\to R_2-3R_1
]

[
R_2=[3,1,7]-3[1,2,4]=[0,-5,-5]
]

[
R_3\to R_3-4R_1
]

[
R_3=[4,-1,7]-4[1,2,4]=[0,-9,-9]
]

[
R_4\to R_4-4R_1
]

[
R_4=[4,-1,5]-4[1,2,4]=[0,-9,-11]
]

So:

[
\begin{bmatrix}
1&2&4\
0&-5&-5\
0&-9&-9\
0&-9&-11
\end{bmatrix}
]

## Step 3: Make entries below second pivot zero

Use:

[
R_2=[0,-5,-5]
]

Clearly,

[
R_3=\frac{9}{5}R_2
]

So:

[
R_3\to 0
]

For (R_4), it will not become zero fully.

Echelon form becomes like:

[
\begin{bmatrix}
1&2&4\
0&-5&-5\
0&0&-2\
0&0&0
\end{bmatrix}
]

## Step 4: Count non-zero rows

There are 3 non-zero rows.

[
\boxed{\text{Rank of }A=3}
]

---

# Solved Example 2 — Gauss elimination method

Solve:

[
x-y+z=4
]

[
2x+y-3z=0
]

[
x+y+z=2
]

## Step 1: Write augmented matrix

[
\left[
\begin{array}{ccc|c}
1&-1&1&4\
2&1&-3&0\
1&1&1&2
\end{array}
\right]
]

## Step 2: Make entries below first pivot zero

[
R_2\to R_2-2R_1
]

[
R_2=[2,1,-3,0]-2[1,-1,1,4]
]

[
R_2=[0,3,-5,-8]
]

[
R_3\to R_3-R_1
]

[
R_3=[1,1,1,2]-[1,-1,1,4]
]

[
R_3=[0,2,0,-2]
]

Now:

[
\left[
\begin{array}{ccc|c}
1&-1&1&4\
0&3&-5&-8\
0&2&0&-2
\end{array}
\right]
]

## Step 3: Make entry below second pivot zero

Use:

[
R_3\to 3R_3-2R_2
]

[
3R_3=[0,6,0,-6]
]

[
2R_2=[0,6,-10,-16]
]

[
R_3=[0,0,10,10]
]

So:

[
\left[
\begin{array}{ccc|c}
1&-1&1&4\
0&3&-5&-8\
0&0&10&10
\end{array}
\right]
]

## Step 4: Back substitution

From third row:

[
10z=10
]

[
z=1
]

From second row:

[
3y-5z=-8
]

[
3y-5=-8
]

[
3y=-3
]

[
y=-1
]

From first row:

[
x-y+z=4
]

[
x-(-1)+1=4
]

[
x+2=4
]

[
x=2
]

[
\boxed{x=2,\ y=-1,\ z=1}
]

---

# 5 Practice questions

## Q1. Rank by echelon form

Find the rank of:

[
A=
\begin{bmatrix}
1&1&2\
1&4&3\
3&3&6
\end{bmatrix}
]

---

## Q2. Gauss elimination

Solve using Gauss elimination:

[
x+3y-2z=0
]

[
2x-y+4z=0
]

[
x-11y+14z=0
]

---

## Q3. Consistency

Determine whether the system is consistent or inconsistent:

[
x-3z=-1
]

[
2x-z=3
]

---

## Q4. Homogeneous system with parameter

Find values of (k) for which the system has only trivial solution:

[
x-ky+z=0
]

[
kx+3y-kz=0
]

[
3x+y-z=0
]

---

## Q5. Gauss-Jordan inverse

Find the inverse using Gauss-Jordan method:

[
A=
\begin{bmatrix}
2&-1&1\
1&1&-1\
1&-2&3
\end{bmatrix}
]

---

# Common mistakes

1. **Confusing row operations with column operations**
   In echelon/Gauss elimination, use row operations unless specifically asked for column rank.

2. **Not writing augmented matrix for system of equations**
   For solving equations, always write:

   [
   [A:B]
   ]

3. **Wrong consistency condition**
   Remember:

   [
   \rho(A)=\rho([A:B])
   ]

   means system is consistent.

4. **For homogeneous system, forgetting determinant condition**
   For square homogeneous system:

   [
   |A|\neq 0 \Rightarrow \text{only trivial solution}
   ]

   [
   |A|=0 \Rightarrow \text{non-trivial solution}
   ]

5. **Stopping Gauss elimination too early**
   You must form upper triangular form, then do back substitution.

6. **In Gauss-Jordan inverse, forgetting to attach identity matrix**
   Always start with:

   [
   [A:I]
   ]

---

# Last-minute revision

Revise these in order:

1. **Rank by echelon form**
2. **Consistency condition using ranks**
3. **Homogeneous system: determinant zero/non-zero**
4. **Gauss elimination steps**
5. **Gauss-Jordan inverse steps**
6. **Inverse method: (X=A^{-1}B)**
7. **Definitions: rank, echelon form, Gauss-Jordan method**

---

# Concept go through

Before exam, remember this flow:

## For rank questions

[
\text{Matrix} \rightarrow \text{Echelon form} \rightarrow \text{Count non-zero rows}
]

## For consistency questions

[
A,\ [A:B] \rightarrow \rho(A),\rho([A:B])
]

Then compare ranks.

## For homogeneous systems

[
AX=0
]

Check determinant:

[
|A|\neq 0 \Rightarrow \text{only trivial solution}
]

[
|A|=0 \Rightarrow \text{non-trivial solution}
]

## For Gauss elimination

[
[A:B]\rightarrow \text{upper triangular form}\rightarrow \text{back substitution}
]

## For Gauss-Jordan inverse

[
[A:I]\rightarrow[I:A^{-1}]
]

This unit is mostly **method-based**, so practice row operations carefully. One correct row operation chain can easily give full marks.
