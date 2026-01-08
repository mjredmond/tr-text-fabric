Doc4TF pages for [Textus Receptus Text Fabric Dataset](https://github.com/mjredmond/tr-text-fabric/tree/master/data/output/tf) (version dataset Jan 7, 2026)
# Overview features by node type
Overview by [name](featuresbyname.md), [data type](featuresbydatatype.md), or [feature type](featuresbytype.md).
## book

Feature|Feature type|Data type|Description|Examples
---|---|---|---|---
[`book`](book.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|book name (full)|`Acts` `Colossians` `Ephesians` `Galatians`
## chapter

Feature|Feature type|Data type|Description|Examples
---|---|---|---|---
[`chapter`](chapter.md#readme)|[`Node`](featuresbytype.md#Node)|[`Integer`](featuresbydatatype.md#Integer)|chapter number|`1` `2` `3` `4`
## verse

Feature|Feature type|Data type|Description|Examples
---|---|---|---|---
[`verse`](verse.md#readme)|[`Node`](featuresbytype.md#Node)|[`Integer`](featuresbydatatype.md#Integer)|verse number|`1` `2` `3` `4`
## clause

Feature|Feature type|Data type|Description|Examples
---|---|---|---|---
[`book`](book.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|book name (full)|`Acts` `Colossians` `Ephesians` `Galatians`
[`chapter`](chapter.md#readme)|[`Node`](featuresbytype.md#Node)|[`Integer`](featuresbydatatype.md#Integer)|chapter number|`1` `2` `3` `4`
[`clausetype`](clausetype.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|clause type|`main` `relative` `content` `nominalized`
[`structure_confidence`](structure_confidence.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|confidence score for structure inference (0-1)|`1.00`
[`structure_source`](structure_source.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|source of structure (direct/inferred/unknown_only)|`direct`
[`typ`](typ.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|syntactic type of phrase/clause|`Voct`
[`verse`](verse.md#readme)|[`Node`](featuresbytype.md#Node)|[`Integer`](featuresbydatatype.md#Integer)|verse number|`1` `2` `3` `4`
## wg

Feature|Feature type|Data type|Description|Examples
---|---|---|---|---
[`after`](after.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|after word feature|` `
[`book`](book.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|book name (full)|`Acts` `Colossians` `Ephesians` `Galatians`
[`bookshort`](bookshort.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|bookshort word feature|`LUK` `ACT` `MAT` `JHN`
[`case`](case.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|case word feature|`nominative` `accusative` `genitive` `dative`
[`chapter`](chapter.md#readme)|[`Node`](featuresbytype.md#Node)|[`Integer`](featuresbydatatype.md#Integer)|chapter number|`1` `2` `3` `4`
[`cls`](cls.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|cls word feature|`verb` `noun` `det` `conj`
[`domain`](domain.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|domain word feature|`092004` `089017` `093001` `033006`
[`function`](function.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|syntactic function of phrase/word group|`Cmpl` `Subj` `Objc` `Pred-Obj`
[`gender`](gender.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|gender word feature|`m` `f` `n`
[`gloss`](gloss.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|gloss word feature|`the` `and, also, likewise` `he, she, it, himself, herself, itself; even, very; same` `(rare)`
[`id`](id.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|id word feature|`n40001001001` `n40001001002` `n40001001003` `n40001001004`
[`lemma`](lemma.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|lemma word feature|`ὁ` `καί` `αὐτός` `σύ`
[`lemmatranslit`](lemmatranslit.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|lemmatranslit word feature|`o` `kai` `autos` `su`
[`ln`](ln.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|ln word feature|`92.24` `89.92` `92.11` `23.50`
[`mood`](mood.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|mood word feature|`indicative` `participle` `infinitive` `imp`
[`morph`](morph.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|morph word feature|`CONJ` `PREP` `ADV` `PRT`
[`normalized`](normalized.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|normalized word feature|`καὶ` `ὁ` `ἐν` `δὲ`
[`num`](num.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|num word feature|`1` `2` `3` `4`
[`number`](number.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|number word feature|`s` `p` `d`
[`parent`](parent.md#readme)|[`Edge`](featuresbytype.md#Edge)|[`Integer`](featuresbydatatype.md#Integer)|parent (head) word in dependency tree|`Link`
[`person`](person.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|person word feature|`2` `3` `1`
[`ref`](ref.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|ref word feature|`1CO 10:1!1` `1CO 10:1!10` `1CO 10:1!11` `1CO 10:1!12`
[`rela`](rela.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|relation to context|`Appo`
[`role`](role.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|role word feature|`adv` `v` `s` `o`
[`rule`](rule.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|syntactic rule for word group|`PrepNp` `DetNP` `NPofNP` `Conj-CL`
[`source`](source.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|source word feature|`n1904` `nlp`
[`sp`](sp.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|sp word feature|`verb` `subs` `art` `conj`
[`strong`](strong.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|strong word feature|`G3588` `G2532` `G846` `G1161`
[`structure_confidence`](structure_confidence.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|confidence score for structure inference (0-1)|`1.00`
[`structure_source`](structure_source.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|source of structure (direct/inferred/unknown_only)|`direct`
[`tense`](tense.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|tense word feature|`present` `aorist` `pres` `past`
[`text`](text.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|text word feature|`καὶ` `ὁ` `ἐν` `δὲ`
[`trailer`](trailer.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|trailer word feature|` `
[`trans`](trans.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|trans word feature|`the` `and` `-` `in`
[`translit`](translit.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|translit word feature|`kai` `o` `en` `to`
[`typ`](typ.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|syntactic type of phrase/clause|`Voct`
[`typems`](typems.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|typems word feature|`common` `personal` `proper` `demonstrative`
[`unaccent`](unaccent.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|unaccent word feature|`και` `ο` `δε` `εν`
[`unicode`](unicode.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|unicode word feature|`καὶ` `ὁ` `ἐν` `δὲ`
[`verse`](verse.md#readme)|[`Node`](featuresbytype.md#Node)|[`Integer`](featuresbydatatype.md#Integer)|verse number|`1` `2` `3` `4`
[`voice`](voice.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|voice word feature|`active` `act` `passive` `middle`
## phrase

Feature|Feature type|Data type|Description|Examples
---|---|---|---|---
[`book`](book.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|book name (full)|`Acts` `Colossians` `Ephesians` `Galatians`
[`chapter`](chapter.md#readme)|[`Node`](featuresbytype.md#Node)|[`Integer`](featuresbydatatype.md#Integer)|chapter number|`1` `2` `3` `4`
[`function`](function.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|syntactic function of phrase/word group|`Cmpl` `Subj` `Objc` `Pred-Obj`
[`structure_confidence`](structure_confidence.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|confidence score for structure inference (0-1)|`1.00`
[`structure_source`](structure_source.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|source of structure (direct/inferred/unknown_only)|`direct`
[`typ`](typ.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|syntactic type of phrase/clause|`Voct`
[`verse`](verse.md#readme)|[`Node`](featuresbytype.md#Node)|[`Integer`](featuresbydatatype.md#Integer)|verse number|`1` `2` `3` `4`
## w

Feature|Feature type|Data type|Description|Examples
---|---|---|---|---
[`after`](after.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|after word feature|` `
[`book`](book.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|book name (full)|`Acts` `Colossians` `Ephesians` `Galatians`
[`bookshort`](bookshort.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|bookshort word feature|`LUK` `ACT` `MAT` `JHN`
[`case`](case.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|case word feature|`nominative` `accusative` `genitive` `dative`
[`chapter`](chapter.md#readme)|[`Node`](featuresbytype.md#Node)|[`Integer`](featuresbydatatype.md#Integer)|chapter number|`1` `2` `3` `4`
[`cls`](cls.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|cls word feature|`verb` `noun` `det` `conj`
[`domain`](domain.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|domain word feature|`092004` `089017` `093001` `033006`
[`gender`](gender.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|gender word feature|`m` `f` `n`
[`gloss`](gloss.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|gloss word feature|`the` `and, also, likewise` `he, she, it, himself, herself, itself; even, very; same` `(rare)`
[`id`](id.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|id word feature|`n40001001001` `n40001001002` `n40001001003` `n40001001004`
[`lemma`](lemma.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|lemma word feature|`ὁ` `καί` `αὐτός` `σύ`
[`lemmatranslit`](lemmatranslit.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|lemmatranslit word feature|`o` `kai` `autos` `su`
[`ln`](ln.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|ln word feature|`92.24` `89.92` `92.11` `23.50`
[`mood`](mood.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|mood word feature|`indicative` `participle` `infinitive` `imp`
[`morph`](morph.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|morph word feature|`CONJ` `PREP` `ADV` `PRT`
[`normalized`](normalized.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|normalized word feature|`καὶ` `ὁ` `ἐν` `δὲ`
[`num`](num.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|num word feature|`1` `2` `3` `4`
[`number`](number.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|number word feature|`s` `p` `d`
[`parent`](parent.md#readme)|[`Edge`](featuresbytype.md#Edge)|[`Integer`](featuresbydatatype.md#Integer)|parent (head) word in dependency tree|`Link`
[`person`](person.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|person word feature|`2` `3` `1`
[`ref`](ref.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|ref word feature|`1CO 10:1!1` `1CO 10:1!10` `1CO 10:1!11` `1CO 10:1!12`
[`role`](role.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|role word feature|`adv` `v` `s` `o`
[`source`](source.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|source word feature|`n1904` `nlp`
[`sp`](sp.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|sp word feature|`verb` `subs` `art` `conj`
[`strong`](strong.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|strong word feature|`G3588` `G2532` `G846` `G1161`
[`tense`](tense.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|tense word feature|`present` `aorist` `pres` `past`
[`text`](text.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|text word feature|`καὶ` `ὁ` `ἐν` `δὲ`
[`trailer`](trailer.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|trailer word feature|` `
[`trans`](trans.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|trans word feature|`the` `and` `-` `in`
[`translit`](translit.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|translit word feature|`kai` `o` `en` `to`
[`typems`](typems.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|typems word feature|`common` `personal` `proper` `demonstrative`
[`unaccent`](unaccent.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|unaccent word feature|`και` `ο` `δε` `εν`
[`unicode`](unicode.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|unicode word feature|`καὶ` `ὁ` `ἐν` `δὲ`
[`verse`](verse.md#readme)|[`Node`](featuresbytype.md#Node)|[`Integer`](featuresbydatatype.md#Integer)|verse number|`1` `2` `3` `4`
[`voice`](voice.md#readme)|[`Node`](featuresbytype.md#Node)|[`String`](featuresbydatatype.md#String)|voice word feature|`active` `act` `passive` `middle`


Created on Jan. 08, 2026 using [Doc4TF version 0.5.2 (July 10, 2024)](https://github.com/tonyjurg/Doc4TF/blob/main/CreateFeatureDoc.ipynb)