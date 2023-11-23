package org.dice_research.config;

import org.dice_research.coref.CoreferenceResolution;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.ApplicationContext;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@CrossOrigin(origins = "*", allowCredentials = "true")
@RequestMapping("/api/v1/")
public class RESTController {

	@Autowired
	ApplicationContext ctx;

	@GetMapping("/test")
	public String ping() {
		return "OK!";
	}

	@GetMapping("/validate")
	public String validate(@RequestParam(value = "text", required = true) String text) {

		CoreferenceResolution coref = new CoreferenceResolution();
		String output = coref.generateCrR(text);
		return output;
	}

}