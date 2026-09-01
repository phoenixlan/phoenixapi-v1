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
            border-radius: 1em;
            box-shadow: 0 0 0.7em #50505070;

            padding: 2em;
		}
	}
</style>