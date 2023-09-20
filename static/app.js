
$("#steps").on("click", function(e){
    e.preventDefault()
    if(e.target.classList.contains('remove-button')){
    e.target.parentElement.remove()
    }
})

$("#ingredients").on("click", function(e){
    e.preventDefault()
    if(e.target.classList.contains('remove-button')){
    e.target.parentElement.remove()
    }
})

$("#add-step").on("click", function(e){
    e.preventDefault()
    totalSteps = $('#steps').children().length 
    $("#steps").append(`
    <div id="step-${totalSteps}">
        <label for="steps-${totalSteps}-step">Step</label>
        <br>
        <textarea class="w-100 mt-2" id="steps-${totalSteps}-step" name="steps-${totalSteps}-step" rows="3">
        </textarea>
        <button class="btn btn-danger remove-button"> Delete step </button>
    </div>
    `)
})


$("#add-ingredient").on("click", function(e){
    e.preventDefault()
    totalSteps = $('#ingredients').children().length 
    $("#ingredients").append(`
    <div id="ingredient-${totalSteps}">
        <div class="grid mx-auto">
        <label for="ingredients-${totalSteps}-amount">Amount</label> <input id="ingredients-${totalSteps}-amount" name="ingredients-${totalSteps}-amount" type="text" value="">
        <label for="ingredients-${totalSteps}-unit">Unit</label> <input id="ingredients-${totalSteps}-unit" name="ingredients-${totalSteps}-unit" type="text" value="">
        <label for="ingredients-${totalSteps}-name">Name</label> <input id="ingredients-${totalSteps}-name" name="ingredients-${totalSteps}-name" type="text" value="">
        </div>
        <button class="btn btn-danger remove-button">Delete ingredient</button>
    </div>
    `)
})

console.log("load")