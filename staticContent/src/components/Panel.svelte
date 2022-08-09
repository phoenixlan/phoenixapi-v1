<div>
    <slot></slot>
</div>

<style>
    div {
        width: 40em;
        max-width: 90%;

        background-color: white;
        
        
    }
    @media (min-width: 640px) {
		div {
            border-radius: 0.3em;
            box-shadow: 0.2em 0.2em 1em #333;

            padding: 2em;
		}
	}
</style>