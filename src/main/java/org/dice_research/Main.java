package org.dice_research;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.context.annotation.ComponentScan;

/**
 * Launches the application as a REST service
 *
 */
@SpringBootApplication
@ComponentScan("org.dice_research")
public class Main {
  public static void main(String[] args) {
    SpringApplication.run(Main.class, args);
  }
}
