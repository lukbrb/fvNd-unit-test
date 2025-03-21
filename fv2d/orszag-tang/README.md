# Vortex de Orszag-Tang

**Description**  
Ce problème a été introduit par Orszag et Tang en 1979, et utilisé fréquemment pour comparer des simulations MHD.

**Caractéristiques**  
Pour ce test nous utilisons un domaine carré, en prenant $0 \leq x \leq 1$ et $0 \leq y \leq 1$ et des conditions périodiques sur les quatres bords. Les conditions initiales pour la densité $\rho=\frac{5\gamma}{12\pi} = \frac{25}{36\pi}$ et la pression $P=\frac{\gamma}{4\pi} = \frac{5}{12\pi}$, en utilisant donc $\gamma=5/3$. Les vitesses initiales sont périodiques, avec $v_x = -\sin(2\pi y)$ et $v_y = -\sin(4\pi x)$. Le champ magnétique initial est lui initialisé en utilisant un vecteur potentiel $A_z = B_0 \left(\dfrac{cos(4\pi x)}{4\pi} + \dfrac{cos(2\pi y)}{2\pi} \right)$ ce qui donne $B_x = -B_0 \sin(2\pi y)$ et $B_y = B_0 \sin(4\pi x)$, avec $B_0=1/\sqrt{4\pi}$.

**Pertinence**  
Ce problème est connu pour tester les transitions vers les turbulences supersoniques en MHD 2D. Notamment, ce problème est utilisé pour vérifier la capacité du code à gérer la formation des chocs MHD et, des intéractions choc-choc. Il permet également de donner des estimations quantitatives sur l'impact des monopoles magnétiques sur la solution, donc de tester la condition $\nabla \cdot B = 0$.

**Résultats**  
La simulation a été réalisée sur une grille de $256 \times 256$, avec une $CFL=0.5$ et un solveur *HLLD*.


https://github.com/user-attachments/assets/8db1a281-e855-42e1-870b-12a1cc333587


Afin de tester quantitativement nos résultats, on trace deux tranches deux notre domaine à $y=0.4277$ et $y=0.3125$ que l'on compare à la figure 11 de Londrillo et Del Zanna (2000)

![](./orszag-tang_slice.png)

Notre résultat semble quantitavement correct et qualitativement proche, mais l'on remarque que notre solveur est davantage diffusif que celui d'Athena. Ceci est notamment dû à l'ordre auquel nous résolvons.

**Références**  
- Test du [vortex Orszag-Tang Athena](https://www.astro.princeton.edu/~jstone/Athena/tests/orszag-tang/pagesource.html)
- [Orszag, S.A., Tang, C.-M., 1979. Small-scale structure of two-dimensional magnetohydrodynamic turbulence. Journal of Fluid Mechanics 90, 129–143.](https://doi.org/10.1017/S002211207900210X)
- [Londrillo, P., Zanna, L.D., 2000. High-Order Upwind Schemes forMultidimensional Magnetohydrodynamics. ApJ 530, 508.](https://doi.org/10.1086/308344)
