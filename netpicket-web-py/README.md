# netpicket-web-py

1. Remember to create db.

2. While testing setup debug mode to avoid OAuth crash:

    ```bash
    export OAUTHLIB_INSECURE_TRANSPORT=1
    ```

3. Add Google client secret:

    ```bash
    export G_CLIENT_SECRET="<the secret>"
    ```

Launch for testing:

```bash
gunicorn --reload -b 127.0.0.1:5000 -k gevent app:app
```

## Notes

See [CVE datasource](http://www.cvedetails.com/).
