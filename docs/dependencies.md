Compontents:

```mermaid
graph TD;
    CloudSQL-->django-east;
    CloudSQL-->django-west;
    django-east-->translator-east;
    translator-east-->goBGP-east;
    goBGP-east-->rtr1;
    django-west-->translator-west;
    translator-west-->goBGP-west;
    goBGP-west-->rtr2;
```
