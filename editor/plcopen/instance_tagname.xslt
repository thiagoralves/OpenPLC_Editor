<?xml version="1.0"?>
<xsl:stylesheet xmlns:exsl="http://exslt.org/common" xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:ppx="http://www.plcopen.org/xml/tc6_0201" xmlns:ns="beremiz" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" extension-element-prefixes="ns" version="1.0" exclude-result-prefixes="ns">
  <xsl:output method="xml"/>
  <xsl:param name="instance_path"/>
  <xsl:variable name="project" select="ns:GetProject()"/>
  <xsl:variable name="stdlib" select="ns:GetStdLibs()"/>
  <xsl:variable name="extensions" select="ns:GetExtensions()"/>
  <xsl:variable name="all_types" select="($project | $stdlib | $extensions)/ppx:types"/>
  <xsl:template name="element_name">
    <xsl:param name="path"/>
    <xsl:choose>
      <xsl:when test="contains($path,'.')">
        <xsl:value-of select="substring-before($path,'.')"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$path"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  <xsl:template name="next_path">
    <xsl:param name="path"/>
    <xsl:choose>
      <xsl:when test="contains($path,'.')">
        <xsl:value-of select="substring-after($path,'.')"/>
      </xsl:when>
    </xsl:choose>
  </xsl:template>
  <xsl:template match="ppx:project">
    <xsl:variable name="config_name">
      <xsl:call-template name="element_name">
        <xsl:with-param name="path" select="$instance_path"/>
      </xsl:call-template>
    </xsl:variable>
    <xsl:apply-templates select="ppx:instances/ppx:configurations/ppx:configuration[@name=$config_name]">
      <xsl:with-param name="element_path">
        <xsl:call-template name="next_path">
          <xsl:with-param name="path" select="$instance_path"/>
        </xsl:call-template>
      </xsl:with-param>
    </xsl:apply-templates>
  </xsl:template>
  <xsl:template match="ppx:configuration">
    <xsl:param name="element_path"/>
    <xsl:choose>
      <xsl:when test="$element_path!=''">
        <xsl:variable name="child_name">
          <xsl:call-template name="element_name">
            <xsl:with-param name="path" select="$element_path"/>
          </xsl:call-template>
        </xsl:variable>
        <xsl:apply-templates select="ppx:resource[@name=$child_name] | ppx:globalVars/ppx:variable[@name=$child_name]/ppx:type/*[self::ppx:derived or self::ppx:struct or self::ppx:array]">
          <xsl:with-param name="element_path">
            <xsl:call-template name="next_path">
              <xsl:with-param name="path" select="$element_path"/>
            </xsl:call-template>
          </xsl:with-param>
        </xsl:apply-templates>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="ns:ConfigTagName(@name)"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  <xsl:template match="ppx:resource">
    <xsl:param name="element_path"/>
    <xsl:choose>
      <xsl:when test="$element_path!=''">
        <xsl:variable name="child_name">
          <xsl:call-template name="element_name">
            <xsl:with-param name="path">
              <xsl:value-of select="$element_path"/>
            </xsl:with-param>
          </xsl:call-template>
        </xsl:variable>
        <xsl:apply-templates select="ppx:pouInstance[@name=$child_name] | ppx:task/ppx:pouInstance[@name=$child_name] | ppx:globalVars/ppx:variable[@name=$child_name]/ppx:type/*[self::ppx:derived or self::ppx:struct or self::ppx:array]">
          <xsl:with-param name="element_path">
            <xsl:call-template name="next_path">
              <xsl:with-param name="path" select="$element_path"/>
            </xsl:call-template>
          </xsl:with-param>
        </xsl:apply-templates>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="ns:ResourceTagName(ancestor::ppx:configuration/@name, @name)"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  <xsl:template match="ppx:pouInstance">
    <xsl:param name="element_path"/>
    <xsl:variable name="type_name">
      <xsl:value-of select="@typeName"/>
    </xsl:variable>
    <xsl:apply-templates select="$all_types/ppx:pous/ppx:pou[@name=$type_name] |                  $all_types/ppx:dataTypes/ppx:dataType[@name=$type_name]">
      <xsl:with-param name="element_path" select="$element_path"/>
    </xsl:apply-templates>
  </xsl:template>
  <xsl:template match="ppx:pou">
    <xsl:param name="element_path"/>
    <xsl:choose>
      <xsl:when test="$element_path!=''">
        <xsl:variable name="child_name">
          <xsl:call-template name="element_name">
            <xsl:with-param name="path" select="$element_path"/>
          </xsl:call-template>
        </xsl:variable>
        <xsl:apply-templates select="ppx:interface/*/ppx:variable[@name=$child_name]/ppx:type/*[self::ppx:derived or self::ppx:struct or self::ppx:array]">
          <xsl:with-param name="element_path">
            <xsl:call-template name="next_path">
              <xsl:with-param name="path" select="$element_path"/>
            </xsl:call-template>
          </xsl:with-param>
        </xsl:apply-templates>
        <xsl:apply-templates select="ppx:actions/ppx:action[@name=$child_name] | ppx:transitions/ppx:transition[@name=$child_name]"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:variable name="name">
          <xsl:value-of select="@name"/>
        </xsl:variable>
        <xsl:value-of select="ns:PouTagName($name)"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  <xsl:template match="ppx:action">
    <xsl:value-of select="ns:ActionTagName(ancestor::ppx:pou/@name, @name)"/>
  </xsl:template>
  <xsl:template match="ppx:transition">
    <xsl:value-of select="ns:TransitionTagName(ancestor::ppx:pou/@name, @name)"/>
  </xsl:template>
  <xsl:template match="ppx:dataType">
    <xsl:param name="element_path"/>
    <xsl:apply-templates select="ppx:baseType/*[self::ppx:derived or self::ppx:struct or self::ppx:array]">
      <xsl:with-param name="element_path" select="$element_path"/>
    </xsl:apply-templates>
  </xsl:template>
  <xsl:template match="ppx:derived">
    <xsl:param name="element_path"/>
    <xsl:variable name="type_name">
      <xsl:value-of select="@name"/>
    </xsl:variable>
    <xsl:apply-templates select="$all_types/ppx:pous/ppx:pou[@name=$type_name] |                  $all_types/ppx:dataTypes/ppx:dataType[@name=$type_name]">
      <xsl:with-param name="element_path" select="$element_path"/>
    </xsl:apply-templates>
  </xsl:template>
  <xsl:template match="ppx:array">
    <xsl:param name="element_path"/>
    <xsl:apply-templates select="ppx:baseType/*[self::ppx:derived or self::ppx:struct or self::ppx:array]">
      <xsl:with-param name="element_path" select="$element_path"/>
    </xsl:apply-templates>
  </xsl:template>
  <xsl:template match="ppx:struct">
    <xsl:param name="element_path"/>
    <xsl:variable name="child_name">
      <xsl:call-template name="element_name">
        <xsl:with-param name="path" select="$element_path"/>
      </xsl:call-template>
    </xsl:variable>
    <xsl:apply-templates select="ppx:variable[@name=$child_name]/ppx:type/*[self::ppx:derived or self::ppx:struct or self::ppx:array]">
      <xsl:with-param name="element_path">
        <xsl:call-template name="next_path">
          <xsl:with-param name="path" select="$element_path"/>
        </xsl:call-template>
      </xsl:with-param>
    </xsl:apply-templates>
  </xsl:template>
</xsl:stylesheet>
