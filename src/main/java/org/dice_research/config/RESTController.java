package org.dice_research.config;

import org.dice_research.coref.CoreferenceResolution;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.ApplicationContext;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@CrossOrigin(origins = "*")
public class RESTController {

	@Autowired
	ApplicationContext ctx;
	
	@Autowired
	CoreferenceResolution coref;

	@GetMapping("/test")
	public String ping() {
		return "OK!";
	}

	@GetMapping("/validate")
	public String validate(@RequestParam(value = "text", required = true) String text) {
		return coref.generateCrR(text);
	}

}