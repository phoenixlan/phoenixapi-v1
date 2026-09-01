<script>
    export let url;
</script>

<img src={url ?? "/static/logo.svg"} alt="En kul logo"/>
<style>
    img {
        max-width: 80%;
        width: 30em;
    }
</style>