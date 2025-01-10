Compontents:

```mermaid
graph TD;
    CloudSQL-->django-east;
    CloudSQL-->django-west;
    django-east-->translator-east;
    translator-east-->GoBGP-east;
    goBGP-east-->rtr1;
    django-west-->translator-west;
    translator-west-->GoBGP-west;
    goBGP-west-->rtr2;
```
